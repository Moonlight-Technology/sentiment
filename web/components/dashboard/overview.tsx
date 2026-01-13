"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchDashboardOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, BarChart, Bar } from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle } from "lucide-react";

export function DashboardOverview() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboardOverview });

  if (isLoading || !data) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, idx) => (
          <Skeleton key={idx} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  const { stats, trend, keywords, overview } = data;
  const alertNegativeSpike = stats.negative / Math.max(stats.total, 1) > 0.4;
  const trendData = trend.map((item: any) => ({
    date: item.date,
    positive: item.positive,
    neutral: item.neutral,
    negative: item.negative,
  }));
  const keywordData = keywords.slice(0, 10);
  const sourceDistribution = Object.entries(overview.sources || {}).map(([source, count]) => ({ source, count }));

  return (
    <div className="space-y-6">
      {alertNegativeSpike && (
        <div className="flex items-center gap-3 rounded-xl border border-destructive/40 bg-destructive/10 p-4 text-destructive">
          <AlertTriangle className="h-5 w-5" />
          <div>
            <p className="font-semibold">Negative sentiment spike detected</p>
            <p className="text-sm">Investigate trending topics to mitigate brand risk.</p>
          </div>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Positive</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.positive}</p>
            <p className="text-sm text-muted-foreground">{((stats.positive / stats.total) * 100 || 0).toFixed(1)}% of total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Neutral</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.neutral}</p>
            <p className="text-sm text-muted-foreground">{((stats.neutral / stats.total) * 100 || 0).toFixed(1)}% of total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Negative</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.negative}</p>
            <p className="text-sm text-muted-foreground">{((stats.negative / stats.total) * 100 || 0).toFixed(1)}% of total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Monitored</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.total}</p>
            <p className="text-sm text-muted-foreground">Updated {new Date(stats.updated_at).toLocaleString()}</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Trend</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ left: 0, right: 0 }}>
                <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip />
                <Area type="monotone" dataKey="positive" stackId="1" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.3} />
                <Area type="monotone" dataKey="neutral" stackId="1" stroke="#94a3b8" fill="#94a3b8" fillOpacity={0.3} />
                <Area type="monotone" dataKey="negative" stackId="1" stroke="#f97316" fill="#f97316" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Source Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceDistribution}>
                <XAxis dataKey="source" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} fill="#0ea5e9" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Top Keywords</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          {keywordData.map((keyword: any) => (
            <Badge key={keyword.keyword} variant="secondary">
              {keyword.keyword} · {keyword.count}
            </Badge>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
