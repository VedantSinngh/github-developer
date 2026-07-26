"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormItem, FormLabel, FormControl } from "@/components/ui/form";
import { Skeleton } from "@/components/ui/skeleton";

export default function NewEvaluationPage() {
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [githubUsername, setGithubUsername] = useState("");
  const [repoOwner, setRepoOwner] = useState("");
  const [repoName, setRepoName] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      // Get role profiles
      const rpRes = await fetch("http://localhost:8000/role-profiles", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const roleProfiles = await rpRes.json();
      const role_profile_id = roleProfiles.length > 0 ? roleProfiles[0].id : 1; // Fallback to 1

      // Create evaluation
      const payload = {
        candidate_name: candidateName,
        candidate_email: candidateEmail,
        github_username: githubUsername,
        repo_owner: repoOwner,
        repo_name: repoName,
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        role_profile_id: role_profile_id
      };

      const res = await fetch("http://localhost:8000/evaluations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create evaluation");
      }

      window.location.href = "/dashboard";
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-ink p-12 font-sans relative overflow-hidden">
      {/* Background Lavender Orb */}
      <div className="absolute top-20 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full gradient-orb-lavender pointer-events-none opacity-60"></div>

      <div className="max-w-2xl mx-auto bg-surface-card border border-hairline rounded-xxl p-10 shadow-soft relative z-10 space-y-8">
        <div>
          <span className="text-[12px] uppercase tracking-[0.96px] font-semibold text-muted">
            Evaluation Setup
          </span>
          <h1 className="text-4xl font-serif font-light text-ink tracking-tight mt-1">
            New Candidate Window
          </h1>
          <p className="text-xs text-body mt-1">
            Configure time-boxed window and repository for window-bounded sync.
          </p>
        </div>

        <Form onSubmit={handleSubmit} className="space-y-6">
          {error && <div className="text-red-500 text-sm font-medium text-center">{error}</div>}
          <div className="grid grid-cols-2 gap-4">
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Candidate Name</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Candidate Email</FormLabel>
              <FormControl>
                <Input
                  type="email"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">GitHub Username</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  value={githubUsername}
                  onChange={(e) => setGithubUsername(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Repo Owner</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  value={repoOwner}
                  onChange={(e) => setRepoOwner(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Repo Name</FormLabel>
              <FormControl>
                <Input
                  type="text"
                  value={repoName}
                  onChange={(e) => setRepoName(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">Start Window</FormLabel>
              <FormControl>
                <Input
                  type="datetime-local"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
            <FormItem>
              <FormLabel className="text-[12px] uppercase tracking-[0.96px] text-muted mb-1.5">End Window</FormLabel>
              <FormControl>
                <Input
                  type="datetime-local"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  required
                />
              </FormControl>
            </FormItem>
          </div>

          <Button type="submit" className="w-full rounded-pill shadow-soft mt-2">
            Create Evaluation Window
          </Button>
        </Form>
      </div>
    </div>
  );
}
