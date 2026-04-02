import Anthropic from "@anthropic-ai/sdk";

const globalForAnthropic = globalThis as unknown as {
  anthropic: Anthropic | undefined;
};

export const anthropic =
  globalForAnthropic.anthropic ??
  new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

if (process.env.NODE_ENV !== "production")
  globalForAnthropic.anthropic = anthropic;

export async function generateContent(prompt: string, type: string, tone: string) {
  const systemPrompt = `You are Larry, an expert AI marketing copywriter. Generate ${type} content with a ${tone} tone.
Output only the content — no explanations, no meta-commentary.`;

  const message = await anthropic.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1024,
    system: systemPrompt,
    messages: [{ role: "user", content: prompt }],
  });

  const block = message.content[0];
  return block.type === "text" ? block.text : "";
}
