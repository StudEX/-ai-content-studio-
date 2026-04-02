"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface Content {
  id: string;
  title: string;
  body: string;
  type: string;
  tone: string | null;
  status: string;
  createdAt: string;
}

export default function ContentPage() {
  const [contents, setContents] = useState<Content[]>([]);
  const [prompt, setPrompt] = useState("");
  const [title, setTitle] = useState("");
  const [type, setType] = useState("copy");
  const [tone, setTone] = useState("professional");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetch("/api/content").then((r) => r.json()).then(setContents);
  }, []);

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);

    const res = await fetch("/api/content/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, title, type, tone }),
    });

    if (res.ok) {
      const newContent = await res.json();
      setContents((prev) => [newContent, ...prev]);
      setPrompt("");
      setTitle("");
    }
    setGenerating(false);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Content Studio</h1>
        <p className="text-gray-500">Generate marketing content with AI</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generate New Content</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleGenerate} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Title</label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Content title" required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Type</label>
                <select value={type} onChange={(e) => setType(e.target.value)} className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm">
                  <option value="copy">Marketing Copy</option>
                  <option value="email">Email</option>
                  <option value="social">Social Media</option>
                  <option value="sms">SMS</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tone</label>
                <select value={tone} onChange={(e) => setTone(e.target.value)} className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm">
                  <option value="professional">Professional</option>
                  <option value="casual">Casual</option>
                  <option value="persuasive">Persuasive</option>
                  <option value="informative">Informative</option>
                </select>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Prompt</label>
              <Textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Describe the content you want to generate..." rows={4} required />
            </div>
            <Button type="submit" disabled={generating}>
              {generating ? "Generating..." : "Generate with AI"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Content</h2>
        {contents.length === 0 ? (
          <p className="text-gray-500">No content yet. Generate your first piece above.</p>
        ) : (
          <div className="grid gap-4">
            {contents.map((item) => (
              <Card key={item.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{item.title}</CardTitle>
                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">{item.type}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap text-sm text-gray-700">{item.body}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
