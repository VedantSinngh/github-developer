"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";

export default function CreateCohortPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: "",
    role_level: "",
    tech_stack: "",
    start_date: "",
    end_date: "",
    repo_template_id: 1, // Mocked for now, in a real app would be a dropdown
    role_profile_id: 1,  // Mocked for now
  });
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setUploading(true);
    setError(null);

    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      let candidateIds: number[] = [];

      // 1. Upload candidates CSV if provided
      if (file) {
        const formDataUpload = new FormData();
        formDataUpload.append("file", file);

        const uploadRes = await fetch(`${API_URL}/candidates/bulk-upload`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formDataUpload,
        });

        if (!uploadRes.ok) {
          const errorData = await uploadRes.json();
          throw new Error(errorData.detail || "Failed to upload candidates");
        }
        
        const uploadedCandidates = await uploadRes.json();
        candidateIds = uploadedCandidates.map((c: any) => c.id);
      }

      // 2. Create Cohort
      const cohortRes = await fetch(`${API_URL}/cohorts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: formData.name,
          role_level: formData.role_level,
          tech_stack: formData.tech_stack,
          start_date: new Date(formData.start_date).toISOString(),
          end_date: new Date(formData.end_date).toISOString(),
          repo_template_id: formData.repo_template_id,
          role_profile_id: formData.role_profile_id,
          candidate_ids: candidateIds,
        }),
      });

      if (!cohortRes.ok) {
        const errorData = await cohortRes.json();
        throw new Error(errorData.detail || "Failed to create cohort");
      }

      const newCohort = await cohortRes.json();
      router.push(`/cohorts/${newCohort.id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "An error occurred");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="py-section bg-canvas min-h-screen text-ink font-sans">
      <div className="max-w-3xl mx-auto px-6 space-y-8">
        <header className="border-b border-hairline pb-4">
          <h1 className="text-display-sm font-serif font-light">Create New Cohort</h1>
        </header>

        {error && (
          <div className="p-4 bg-red-100 text-red-800 rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6 bg-surface-card p-6 rounded-xl border border-hairline shadow-soft">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Cohort Name</label>
              <input
                required
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full p-2 border border-hairline rounded bg-canvas focus:ring-1 focus:ring-primary outline-none"
                placeholder="e.g. Q3 Backend Engineers"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Role Level</label>
                <select
                  required
                  name="role_level"
                  value={formData.role_level}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-hairline rounded bg-canvas focus:ring-1 focus:ring-primary outline-none"
                >
                  <option value="">Select Level</option>
                  <option value="Junior">Junior</option>
                  <option value="Mid">Mid</option>
                  <option value="Senior">Senior</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Tech Stack</label>
                <input
                  required
                  type="text"
                  name="tech_stack"
                  value={formData.tech_stack}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-hairline rounded bg-canvas focus:ring-1 focus:ring-primary outline-none"
                  placeholder="e.g. Python, FastAPI"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Start Date</label>
                <input
                  required
                  type="datetime-local"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-hairline rounded bg-canvas focus:ring-1 focus:ring-primary outline-none"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">End Date</label>
                <input
                  required
                  type="datetime-local"
                  name="end_date"
                  value={formData.end_date}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-hairline rounded bg-canvas focus:ring-1 focus:ring-primary outline-none"
                />
              </div>
            </div>

            <div className="pt-4 border-t border-hairline">
              <label className="block text-sm font-medium mb-1">Upload Candidates (CSV)</label>
              <p className="text-xs text-muted mb-2">CSV must include columns: name, email, github_username</p>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="w-full p-2 border border-hairline rounded bg-canvas focus:ring-1 focus:ring-primary outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-6 border-t border-hairline">
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="px-4 py-2 border border-hairline rounded-pill hover:bg-canvas-soft transition-colors text-sm font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="px-4 py-2 bg-primary text-on-primary rounded-pill hover:bg-primary-active transition-colors text-sm font-medium disabled:opacity-50"
            >
              {uploading ? "Creating..." : "Create Cohort"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
