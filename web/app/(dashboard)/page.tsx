import { DashboardOverview } from "@/components/dashboard/overview";

export default function Page() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm text-muted-foreground">Overview</p>
        <h2 className="text-3xl font-bold">Sentiment Pulse</h2>
      </div>
      <DashboardOverview />
    </section>
  );
}
