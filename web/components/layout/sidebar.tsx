"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  Rss,
  LineChart,
  Settings,
  Palette,
  ShieldCheck,
  Bot,
} from "lucide-react";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/users", label: "Users", icon: Users },
  { href: "/sources", label: "Sources", icon: Rss },
  { href: "/sentiment", label: "Sentiment", icon: Bot },
  { href: "/reports", label: "Reports", icon: LineChart },
  { href: "/branding", label: "Branding", icon: Palette },
  { href: "/security", label: "Security", icon: ShieldCheck },
  { href: "/system", label: "System", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-64 flex-col border-r bg-muted/30 p-4 md:flex">
      <div className="mb-6">
        <p className="text-sm text-muted-foreground">Sentiment Analysis</p>
        <h1 className="text-2xl font-semibold">Command Center</h1>
      </div>
      <nav className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
