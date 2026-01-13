"use client";

import useSWR from "swr";
import { apiClient } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

const fetcher = (url: string) => apiClient.get(url).then((res) => res.data);

export default function SecurityPage() {
  const { data: logs, isLoading } = useSWR("/audit/logs", fetcher);
  const { data: roles } = useSWR("/roles", fetcher);

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Security & Access</p>
          <h2 className="text-3xl font-semibold">Security</h2>
        </div>
        <Button>Tambah Role</Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Roles</CardTitle>
        </CardHeader>
        <CardContent>
          {roles ? (
            <div className="grid gap-4 md:grid-cols-2">
              {(roles as any[]).map((role: any) => (
                <div key={role.id} className="rounded-lg border p-3">
                  <p className="font-semibold">{role.name}</p>
                  <p className="text-xs text-muted-foreground">Permissions: {role.permissions.join(", ")}</p>
                </div>
              ))}
            </div>
          ) : (
            <Skeleton className="h-24" />
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Audit Logs</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Action</TableHead>
                  <TableHead>Message</TableHead>
                  <TableHead>Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs?.map((log: any) => (
                  <TableRow key={log.id}>
                    <TableCell>{log.action}</TableCell>
                    <TableCell>{log.message}</TableCell>
                    <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
