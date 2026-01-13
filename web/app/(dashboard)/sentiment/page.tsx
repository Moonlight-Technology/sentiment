"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchContents,
  fetchContentHistory,
  fetchKeywordSentiment,
  fetchBrandSentiment,
  runSentiment,
  runSentimentForItem,
  updateContentLabel,
} from "@/lib/api";
import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { Textarea } from "@/components/ui/textarea";

type KeywordStats = {
  keyword: string;
  positive: number;
  neutral: number;
  negative: number;
  total: number;
  updated_at: string;
};

export default function SentimentPage() {
  const [filters, setFilters] = useState({ keyword: "" });
  const [keywordQuery, setKeywordQuery] = useState("");
  const [keywordStats, setKeywordStats] = useState<KeywordStats | null>(null);
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [overrideLabel, setOverrideLabel] = useState("");
  const [brandLabel, setBrandLabel] = useState("");
  const [brandStats, setBrandStats] = useState<any | null>(null);
  const queryClient = useQueryClient();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["contents", filters],
    queryFn: () => fetchContents({ keyword: filters.keyword }),
  });

  const sentimentMutation = useMutation({
    mutationFn: () => runSentiment(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["contents"] });
    },
  });

  const keywordMutation = useMutation({
    mutationFn: (keyword: string) => fetchKeywordSentiment(keyword, true),
    onSuccess: (data) => {
      setKeywordStats(data);
      toast.success("Keyword sentiment updated");
    },
    onError: () => toast.error("Gagal mengambil data keyword"),
  });

  const runItemMutation = useMutation({
    mutationFn: (id: string) => runSentimentForItem(id),
    onMutate: (id) => setActiveItemId(id),
    onSuccess: () => {
      toast.success("Sentimen dihitung");
      queryClient.invalidateQueries({ queryKey: ["contents"] });
    },
    onError: () => toast.error("Gagal menjalankan sentimen"),
    onSettled: () => setActiveItemId(null),
  });

  return (
    <section className="space-y-4">
      {(sentimentMutation.isPending || runItemMutation.isPending) && (
        <div className="rounded-lg border bg-secondary/40 p-3">
          <p className="text-sm font-medium">
            {sentimentMutation.isPending
              ? "Sedang menjalankan batch sentiment..."
              : "Sedang memproses item terpilih..."}
          </p>
          <progress className="mt-2 h-2 w-full" />
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Monitor latest scored content</p>
          <h2 className="text-3xl font-semibold">Sentiment Processing</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <Input
            placeholder="Cari kata kunci"
            value={filters.keyword}
            onChange={(e) => setFilters((prev) => ({ ...prev, keyword: e.target.value }))}
            className="w-64"
          />
          <Button onClick={() => refetch()}>Cari</Button>
          <Button variant="outline" onClick={() => sentimentMutation.mutate()} disabled={sentimentMutation.isPending}>
            {sentimentMutation.isPending ? "Memproses..." : "Run Sentiment"}
          </Button>
        </div>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Konten Terkini</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-48" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Judul</TableHead>
                  <TableHead>Sumber</TableHead>
                  <TableHead>Sentimen</TableHead>
                  <TableHead>Skor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.map((item: any) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <div className="font-medium">{item.title || "Untitled"}</div>
                      <p className="text-xs text-muted-foreground overflow-hidden text-ellipsis">
                        {item.body}
                      </p>
                    </TableCell>
                    <TableCell>{item.source_type}</TableCell>
                    <TableCell>
                      {item.sentiment ? (
                        <Badge variant={item.sentiment.label === "negative" ? "destructive" : "secondary"}>
                          {item.sentiment.label}
                        </Badge>
                      ) : (
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">Pending</Badge>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => runItemMutation.mutate(item.id)}
                            disabled={runItemMutation.isPending && activeItemId === item.id}
                          >
                            {runItemMutation.isPending && activeItemId === item.id ? "Memproses" : "Score"}
                          </Button>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{item.sentiment?.score?.toFixed(2) ?? "-"}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={async () => {
                          setSelectedItem(item);
                          setOverrideLabel(item.sentiment?.label || "");
                          const historyData = await fetchContentHistory(item.id);
                          setHistory(historyData);
                        }}
                      >
                        Detail
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Sentimen Berdasarkan Keyword</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Contoh: bbm, inflasi, pemilu"
              value={keywordQuery}
              onChange={(e) => setKeywordQuery(e.target.value)}
              className="w-64"
            />
            <Button
              variant="secondary"
              onClick={() => keywordMutation.mutate(keywordQuery)}
              disabled={!keywordQuery || keywordMutation.isPending}
            >
              {keywordMutation.isPending ? "Mencari..." : "Dapatkan Sentimen"}
            </Button>
          </div>
          {keywordStats ? (
            <div className="grid gap-4 md:grid-cols-4">
              <StatCard label="Keyword" value={keywordStats.keyword} subtitle={`Updated ${new Date(keywordStats.updated_at).toLocaleString()}`} />
              <StatCard label="Positive" value={keywordStats.positive.toString()} />
              <StatCard label="Neutral" value={keywordStats.neutral.toString()} />
              <StatCard label="Negative" value={keywordStats.negative.toString()} />
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Masukkan keyword untuk melihat ringkasan sentimen.</p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Brand Sentiment</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Label brand (mis. brand_x)"
              value={brandLabel}
              onChange={(e) => setBrandLabel(e.target.value)}
              className="w-64"
            />
            <Button
              variant="outline"
              disabled={!brandLabel}
              onClick={async () => {
                try {
                  const data = await fetchBrandSentiment(brandLabel);
                  setBrandStats(data);
                } catch (error) {
                  toast.error("Gagal memuat brand sentiment");
                }
              }}
            >
              Tampilkan
            </Button>
          </div>
          {brandStats ? (
            <div className="space-y-3">
              <div className="grid gap-4 md:grid-cols-4">
                <StatCard label="Positive" value={brandStats.positive} />
                <StatCard label="Neutral" value={brandStats.neutral} />
                <StatCard label="Negative" value={brandStats.negative} />
                <StatCard label="Total" value={brandStats.total} />
              </div>
              <div className="space-y-2">
                <p className="text-sm font-semibold">Contoh Konten</p>
                <div className="space-y-2">
                  {brandStats.top_items.map((item: any) => (
                    <div key={item.id} className="rounded border p-2 text-sm">
                      <p className="font-semibold">{item.title || item.id}</p>
                      <p className="text-muted-foreground text-xs">{item.sentiment?.label || "Pending"}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Masukkan label yang sudah ditandai di konten (misalnya brand).</p>
          )}
        </CardContent>
      </Card>
      <AlertDialog open={Boolean(selectedItem)} onOpenChange={(open) => !open && setSelectedItem(null)}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle>{selectedItem?.title || "Detail Konten"}</AlertDialogTitle>
            <AlertDialogDescription>
              {selectedItem?.body?.slice(0, 200)}...
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-semibold">Riwayat Sentimen</p>
              <div className="max-h-48 overflow-y-auto">
                {history.map((entry) => (
                  <div key={entry.scored_at} className="flex justify-between text-sm border-b py-1">
                    <span>{entry.label.toUpperCase()}</span>
                    <span>{(entry.score * 100).toFixed(1)}%</span>
                    <span>{new Date(entry.scored_at).toLocaleString()}</span>
                  </div>
                ))}
                {history.length === 0 && <p className="text-xs text-muted-foreground">Belum ada histori.</p>}
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold">Override Label</p>
              <Textarea
                value={overrideLabel}
                placeholder="positive / neutral / negative"
                onChange={(e) => setOverrideLabel(e.target.value)}
              />
              <Button
                size="sm"
                onClick={async () => {
                  if (!selectedItem) return;
                  await updateContentLabel(selectedItem.id, overrideLabel);
                  toast.success("Label diperbarui");
                  setSelectedItem(null);
                  queryClient.invalidateQueries({ queryKey: ["contents"] });
                }}
              >
                Simpan
              </Button>
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Batal</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}

function StatCard({ label, value, subtitle }: { label: string; value: string; subtitle?: string }) {
  return (
    <div className="rounded-lg border bg-background p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold">{value}</p>
      {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
    </div>
  );
}
