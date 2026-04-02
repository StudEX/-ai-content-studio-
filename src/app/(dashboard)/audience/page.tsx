"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface Audience {
  id: string;
  name: string;
  description: string | null;
  size: number;
  createdAt: string;
}

export default function AudiencePage() {
  const [audiences, setAudiences] = useState<Audience[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    fetch("/api/audiences").then((r) => r.json()).then(setAudiences);
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/audiences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, description }),
    });
    if (res.ok) {
      const audience = await res.json();
      setAudiences((prev) => [audience, ...prev]);
      setName("");
      setDescription("");
      setShowForm(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Audiences</h1>
          <p className="text-gray-500">Manage your audience segments</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "New Audience"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Audience Segment</CardTitle></CardHeader>
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
              <Button type="submit">Create Segment</Button>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {audiences.length === 0 ? (
          <p className="text-gray-500">No audience segments yet.</p>
        ) : (
          audiences.map((a) => (
            <Card key={a.id}>
              <CardHeader>
                <CardTitle className="text-base">{a.name}</CardTitle>
              </CardHeader>
              <CardContent>
                {a.description && <p className="text-sm text-gray-600 mb-2">{a.description}</p>}
                <p className="text-sm text-gray-500">{a.size} members</p>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
