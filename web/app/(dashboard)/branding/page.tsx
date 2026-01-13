"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchBranding } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function BrandingPage() {
  const { data, isLoading } = useQuery({ queryKey: ["branding"], queryFn: fetchBranding });

  return (
    <section className="space-y-4">
      <div>
        <p className="text-sm text-muted-foreground">White-label configuration</p>
        <h2 className="text-3xl font-semibold">Branding</h2>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Identitas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <Skeleton className="h-20" />
          ) : (
            <>
              <div className="space-y-2">
                <Label>Nama Organisasi</Label>
                <Input defaultValue={data?.branding.organization} placeholder="Nama" />
              </div>
              <div className="space-y-2">
                <Label>Primary Color</Label>
                <Input type="color" defaultValue={data?.branding.primary_color} className="h-10 w-20" />
              </div>
              <div className="space-y-2">
                <Label>Logo URL</Label>
                <Input defaultValue={data?.branding.logo_url} placeholder="https://" />
              </div>
              <Button>Simpan</Button>
            </>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Template Laporan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {isLoading ? (
            <Skeleton className="h-20" />
          ) : (
            <>
              <div>
                <Label>Header</Label>
                <Input defaultValue={data?.template.header} />
              </div>
              <div>
                <Label>Footer</Label>
                <Input defaultValue={data?.template.footer} />
              </div>
              <Button variant="outline">Update Template</Button>
            </>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
