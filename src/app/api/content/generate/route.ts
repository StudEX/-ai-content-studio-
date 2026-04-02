import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { prisma } from "@/lib/db/prisma";
import { generateContent } from "@/lib/ai/client";

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { prompt, title, type, tone } = await req.json();

  if (!prompt || !title) {
    return NextResponse.json({ error: "Prompt and title are required" }, { status: 400 });
  }

  const body = await generateContent(prompt, type || "copy", tone || "professional");

  const content = await prisma.content.create({
    data: {
      title,
      body,
      type: type || "copy",
      tone: tone || "professional",
      prompt,
      userId: session.user.id,
    },
  });

  return NextResponse.json(content, { status: 201 });
}
