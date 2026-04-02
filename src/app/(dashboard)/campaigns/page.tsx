"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface Campaign {
  id: string;
  name: string;
  description: string | null;
  status: string;
  type: string;
  createdAt: string;
  _count?: { contents: number };
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState("email");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/campaigns").then((r) => r.json()).then(setCampaigns);
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    const res = await fetch("/api/campaigns", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description, type }),
    });

    if (res.ok) {
      const campaign = await res.json();
      setCampaigns((prev) => [campaign, ...prev]);
      setName("");
      setDescription("");
      setShowForm(false);
    }
    setLoading(false);
  }

  const statusColors: Record<string, string> = {
    draft: "bg-gray-100 text-gray-700",
    active: "bg-green-100 text-green-700",
    paused: "bg-yellow-100 text-yellow-700",
    completed: "bg-blue-100 text-blue-700",
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Campaigns</h1>
          <p className="text-gray-500">Manage your marketing campaigns</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "New Campaign"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Campaign</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <Input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Description</label>
                <Textarea value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Type</label>
                <select value={type} onChange={(e) => setType(e.target.value)} className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm">
                  <option value="email">Email</option>
                  <option value="social">Social Media</option>
                  <option value="sms">SMS</option>
                </select>
              </div>
              <Button type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create Campaign"}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {campaigns.length === 0 ? (
          <p className="text-gray-500">No campaigns yet.</p>
        ) : (
          campaigns.map((c) => (
            <Card key={c.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{c.name}</CardTitle>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full px-2 py-1 text-xs">{c.type}</span>
                    <span className={`rounded-full px-2 py-1 text-xs ${statusColors[c.status] || ""}`}>{c.status}</span>
                  </div>
                </div>
              </CardHeader>
              {c.description && (
                <CardContent>
                  <p className="text-sm text-gray-600">{c.description}</p>
                </CardContent>
              )}
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
