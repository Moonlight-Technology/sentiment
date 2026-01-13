"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createSource, fetchSources, reloadSources, uploadTwitterCsv } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { toast } from "sonner";

export default function SourcesPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["sources"], queryFn: fetchSources });
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "",
    type: "rss",
    url: "",
    schedule: "daily",
    status: "active",
  });
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvLimit, setCsvLimit] = useState(10000);

  const createMutation = useMutation({
    mutationFn: () => {
      const config: Record<string, string> = {};
      if (form.type === "csv") {
        config.path = form.url;
      } else {
        config.url = form.url;
      }
      return createSource({
        name: form.name,
        type: form.type,
        config,
        schedule: form.schedule,
        status: form.status,
      });
    },
    onSuccess: () => {
      toast.success("Source created");
      setShowForm(false);
      setForm({ name: "", type: "rss", url: "", schedule: "daily", status: "active" });
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: () => toast.error("Failed to create source"),
  });

  const reloadMutation = useMutation({
    mutationFn: reloadSources,
    onSuccess: (data) => {
      toast.success(`Re-crawl triggered (${data.count} sources)`);
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: () => toast.error("Failed to trigger re-crawl"),
  });

  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!csvFile) {
        throw new Error("CSV file required");
      }
      return uploadTwitterCsv(csvFile, csvLimit || undefined);
    },
    onSuccess: (data) => {
      toast.success(`Imported ${data.inserted} tweets (skipped ${data.skipped})`);
      setCsvFile(null);
      queryClient.invalidateQueries({ queryKey: ["sources"], exact: false });
    },
    onError: () => toast.error("Failed to import CSV"),
  });

  return (
    <section className="space-y-4">
      {(reloadMutation.isPending || uploadMutation.isPending) && (
        <div className="rounded-lg border bg-secondary/40 p-3">
          <p className="text-sm font-medium">
            {reloadMutation.isPending ? "Re-crawl in progress..." : "Uploading CSV..."}
          </p>
          <progress className="mt-2 h-2 w-full" />
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Manage data feeds</p>
          <h2 className="text-3xl font-semibold">Sources</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <Input placeholder="Filter by name" className="w-56" disabled />
          <Button variant="outline" onClick={() => reloadMutation.mutate()} disabled={reloadMutation.isPending}>
            {reloadMutation.isPending ? "Reloading..." : "Re-crawl"}
          </Button>
          <Button onClick={() => setShowForm((prev) => !prev)}>{showForm ? "Tutup" : "Tambah Source"}</Button>
        </div>
      </div>
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Source Baru</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              className="grid gap-4 md:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                if (!form.name || !form.url) {
                  toast.error("Nama dan URL wajib diisi");
                  return;
                }
                createMutation.mutate();
              }}
            >
              <div className="space-y-2">
                <label className="text-sm font-medium">Nama</label>
                <Input value={form.name} onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))} required />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Tipe</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.type}
                  onChange={(e) => setForm((prev) => ({ ...prev, type: e.target.value }))}
                >
                  <option value="rss">RSS</option>
                  <option value="twitter">Twitter/X</option>
                  <option value="instagram">Instagram</option>
                  <option value="csv">CSV File</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  {form.type === "csv" ? "CSV File Path" : "Feed / Token URL"}
                </label>
                <Input
                  placeholder={form.type === "csv" ? "data/custom_source.csv" : "https://"}
                  value={form.url}
                  onChange={(e) => setForm((prev) => ({ ...prev, url: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Jadwal</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.schedule}
                  onChange={(e) => setForm((prev) => ({ ...prev, schedule: e.target.value }))}
                >
                  <option value="manual">Manual</option>
                  <option value="daily">Harian</option>
                  <option value="weekly">Mingguan</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                  value={form.status}
                  onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              <div className="flex items-end gap-2">
                <Button type="submit" disabled={createMutation.isPending} className="w-full">
                  {createMutation.isPending ? "Menyimpan..." : "Simpan"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Import Twitter CSV</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-3 md:flex-row md:items-end"
            onSubmit={(e) => {
              e.preventDefault();
              uploadMutation.mutate();
            }}
          >
            <div className="space-y-2">
              <label className="text-sm font-medium">CSV File</label>
              <Input type="file" accept=".csv" onChange={(e) => setCsvFile(e.target.files?.[0] || null)} />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Limit (opsional)</label>
              <Input
                type="number"
                min={1}
                value={csvLimit}
                onChange={(e) => setCsvLimit(parseInt(e.target.value, 10) || 0)}
                className="w-32"
              />
            </div>
            <Button type="submit" disabled={!csvFile || uploadMutation.isPending}>
              {uploadMutation.isPending ? "Mengimpor..." : "Upload & Import"}
            </Button>
          </form>
          {uploadMutation.isPending && <progress className="mt-3 h-2 w-full" />}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Source List</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-32" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nama</TableHead>
                  <TableHead>Tipe</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Terakhir Run</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.map((source: any) => (
                  <TableRow key={source.id}>
                    <TableCell className="font-medium">{source.name}</TableCell>
                    <TableCell>{source.type}</TableCell>
                    <TableCell>
                      <Badge variant={source.status === "active" ? "default" : "secondary"}>{source.status}</Badge>
                    </TableCell>
                    <TableCell>{source.last_run ? new Date(source.last_run).toLocaleString() : "-"}</TableCell>
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
