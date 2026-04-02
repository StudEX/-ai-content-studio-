import { prisma } from "@/lib/db/prisma";
import { auth } from "@/lib/auth";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { FileText, Megaphone, Users, TrendingUp } from "lucide-react";

export default async function AnalyticsPage() {
  const session = await auth();
  const userId = session!.user!.id!;

  const [contentCount, campaignCount, audienceCount, recentContent] = await Promise.all([
    prisma.content.count({ where: { userId } }),
    prisma.campaign.count({ where: { userId } }),
    prisma.audience.count({ where: { userId } }),
    prisma.content.findMany({
      where: { userId },
      orderBy: { createdAt: "desc" },
      take: 5,
    }),
  ]);

  const stats = [
    { label: "Total Content", value: contentCount, icon: FileText, color: "text-blue-600 bg-blue-50" },
    { label: "Campaigns", value: campaignCount, icon: Megaphone, color: "text-green-600 bg-green-50" },
    { label: "Audiences", value: audienceCount, icon: Users, color: "text-purple-600 bg-purple-50" },
    { label: "This Month", value: contentCount, icon: TrendingUp, color: "text-orange-600 bg-orange-50" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">Analytics</h1>
        <p className="text-gray-500">Your marketing performance at a glance</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="flex items-center gap-4 p-6">
                <div className={`rounded-lg p-3 ${stat.color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Content</CardTitle>
        </CardHeader>
        <CardContent>
          {recentContent.length === 0 ? (
            <p className="text-gray-500">No content created yet.</p>
          ) : (
            <div className="space-y-3">
              {recentContent.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-md border border-gray-100 p-3">
                  <div>
                    <p className="font-medium text-sm">{item.title}</p>
                    <p className="text-xs text-gray-500">{item.type} &middot; {new Date(item.createdAt).toLocaleDateString()}</p>
                  </div>
                  <span className="rounded-full bg-gray-100 px-2 py-1 text-xs">{item.status}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
