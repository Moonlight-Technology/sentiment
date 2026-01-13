"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchReports } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

export default function ReportsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["reports"], queryFn: fetchReports });

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Analytics & Reporting</p>
          <h2 className="text-3xl font-semibold">Reports</h2>
        </div>
        <Button>Generate Laporan</Button>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Ringkasan</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sumber</TableHead>
                  <TableHead>Jumlah</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(data?.sources || {}).map(([source, count]) => (
                  <TableRow key={source}>
                    <TableCell className="font-medium">{source}</TableCell>
                    <TableCell>{count as number}</TableCell>
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
