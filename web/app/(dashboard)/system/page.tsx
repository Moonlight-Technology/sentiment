"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchSystemStatus } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function SystemPage() {
  const { data, isLoading } = useQuery({ queryKey: ["system"], queryFn: fetchSystemStatus });

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Ops & Maintenance</p>
          <h2 className="text-3xl font-semibold">System Status</h2>
        </div>
        <Button variant="outline">Backup Manual</Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Infra</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">API Status</p>
                <p className="text-2xl font-semibold">{data?.status.status ?? "unknown"}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Ingested Items</p>
                <p className="text-2xl font-semibold">{data?.status.ingested_items ?? 0}</p>
              </div>
              <div className="rounded-lg border p-4">
                <p className="text-sm text-muted-foreground">Pending Sentiment</p>
                <p className="text-2xl font-semibold">{data?.status.pending_sentiments ?? 0}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Logs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {isLoading ? (
            <Skeleton className="h-24" />
          ) : (
            data?.logs?.logs?.map((log: any) => (
              <div key={log.id} className="rounded border bg-background p-2 text-sm">
                <p className="font-semibold">{log.action}</p>
                <p className="text-muted-foreground">{log.message}</p>
                <p className="text-xs">{new Date(log.timestamp).toLocaleString()}</p>
              </div>
            )) ?? <p className="text-sm text-muted-foreground">No logs available.</p>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
