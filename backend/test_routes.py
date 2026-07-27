"""
Pytest API Route Tests for Candidate Evaluation Platform using httpx AsyncClient.
"""

from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import patch, AsyncMock
from sqlalchemy import select
from main import app, async_session
from models import GitHubConnection


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_and_evaluation_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register Recruiter
        reg_payload = {
            "email": "recruiter@example.com",
            "password": "Password123!",
            "org_name": "Acme Corp",
        }
        reg_res = await ac.post("/auth/register", json=reg_payload)
        assert reg_res.status_code == 201

        # 2. Login Recruiter
        login_res = await ac.post("/auth/login", json={"email": "recruiter@example.com", "password": "Password123!"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create Role Profile
        rp_payload = {
            "name": "Backend Senior",
            "description": "Standard test profile",
            "weight_consistency": 0.2,
            "weight_pr_quality": 0.25,
            "weight_review_cycles": 0.2,
            "weight_collaboration": 0.15,
            "weight_stability": 0.2,
        }
        rp_res = await ac.post("/role-profiles", json=rp_payload, headers=headers)
        assert rp_res.status_code == 201
        rp_id = rp_res.json()["id"]

        # 4. Create Evaluation
        start_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        end_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
        eval_payload = {
            "candidate_name": "Jane Doe",
            "candidate_email": "jane@example.com",
            "github_username": "janedoe",
            "repo_owner": "acme",
            "repo_name": "takehome-project",
            "start_date": start_date,
            "end_date": end_date,
            "role_profile_id": rp_id,
        }
        eval_res = await ac.post("/evaluations", json=eval_payload, headers=headers)
        assert eval_res.status_code == 201
        eval_id = eval_res.json()["id"]

        # 5. Activate Evaluation
        act_res = await ac.post(f"/evaluations/{eval_id}/activate", headers=headers)
        assert act_res.status_code == 200
        assert act_res.json()["status"] == "active"

        # 6. Fetch Score
        score_res = await ac.get(f"/evaluations/{eval_id}/score", headers=headers)
        assert score_res.status_code == 200
        assert score_res.json()["status"] == "active"

        # 7. Fetch Report Card PDF
        report_res = await ac.get(f"/evaluations/{eval_id}/report", headers=headers)
        assert report_res.status_code == 200
        assert report_res.headers["content-type"] == "application/pdf"

@pytest.mark.asyncio
async def test_github_oauth_callback():
    mock_post = AsyncMock()
    mock_post.return_value.json.return_value = {
        "access_token": "mocked_github_token_123",
        "scope": "repo"
    }

    with patch("httpx.AsyncClient.post", new=mock_post), \
         patch("os.getenv", side_effect=lambda k, default=None: "mock_val" if k in ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET", "GITHUB_ENCRYPTION_KEY"] else default):
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/auth/github/callback?code=mock_code&state=1")
            
            # Since it redirects on success, check for 307 Temporary Redirect
            assert res.status_code == 307
            assert "dashboard?github_connected=true" in res.headers["location"]

            # Verify the token is encrypted in the DB
            async with async_session() as session:
                db_res = await session.execute(select(GitHubConnection).where(GitHubConnection.evaluation_id == 1))
                conn = db_res.scalar_one_or_none()
                assert conn is not None
                assert conn.access_token != "mocked_github_token_123"
                assert len(conn.access_token) > 20 # Fernet tokens are long
