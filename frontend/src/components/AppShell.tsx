"use client";

import { LayoutDashboard, LogOut, Plus } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Skeleton } from "@/components/ui/primitives";
import { cn, initials } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";

/** Wraps authenticated pages: redirects to /login when there is no token. */
export function AppShell({
  children,
  /** Interview room manages its own full-height layout, so it opts out of the container. */
  bare = false,
}: {
  children: React.ReactNode;
  bare?: boolean;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, user, hydrated, logout, refresh } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!token) router.replace("/login");
    else void refresh();
  }, [hydrated, token, router, refresh]);

  // Before hydration we cannot know whether the user is signed in. Showing the chrome
  // with skeletons avoids a full-page flash and a layout jump once the token resolves.
  if (!hydrated || !token) {
    return (
      <div className="flex min-h-full flex-1 flex-col">
        <TopBarShell />
        <div className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
          <Skeleton className="h-8 w-52" />
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-28 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="sticky top-0 z-40 border-b border-line-subtle bg-canvas/70 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center gap-5 px-6 py-2.5">
          <Link href="/dashboard" className="text-[0.9375rem] font-semibold tracking-tight">
            Interview<span className="text-accent-bright">Pilot</span>
          </Link>

          <nav className="flex items-center gap-1" aria-label="Main">
            <NavLink href="/dashboard" active={pathname === "/dashboard"} icon={LayoutDashboard}>
              Dashboard
            </NavLink>
            <NavLink href="/interview/new" active={pathname.startsWith("/interview/new")} icon={Plus}>
              New interview
            </NavLink>
          </nav>

          <div className="relative ml-auto">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              onBlur={() => window.setTimeout(() => setMenuOpen(false), 120)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex items-center gap-2 rounded-sm py-1 pr-1 pl-2 transition-colors hover:bg-surface-2"
            >
              <span className="hidden max-w-40 truncate text-sm text-ink-secondary sm:block">
                {user?.full_name || user?.email}
              </span>
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent-dim text-[0.6875rem] font-semibold text-accent-bright">
                {initials(user?.full_name, user?.email ?? "?")}
              </span>
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="surface-edge-lg absolute right-0 z-50 mt-2 w-52 overflow-hidden rounded-md border border-line bg-surface-2 py-1"
              >
                <p className="truncate px-3 py-2 text-xs text-ink-tertiary">{user?.email}</p>
                <div className="my-1 h-px bg-line-subtle" />
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    logout();
                    router.replace("/login");
                  }}
                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-ink-secondary transition-colors hover:bg-surface-3 hover:text-ink"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className={cn("flex-1", !bare && "mx-auto w-full max-w-6xl px-6 py-8")}>{children}</div>
    </div>
  );
}

function TopBarShell() {
  return (
    <header className="border-b border-line-subtle">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-5 px-6 py-2.5">
        <span className="text-[0.9375rem] font-semibold tracking-tight">
          Interview<span className="text-accent-bright">Pilot</span>
        </span>
        <Skeleton className="h-7 w-28 rounded-sm" />
        <Skeleton className="ml-auto h-7 w-7 rounded-full" />
      </div>
    </header>
  );
}

function NavLink({
  href,
  active,
  icon: Icon,
  children,
}: {
  href: string;
  active: boolean;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm px-2.5 py-1.5 text-[0.8125rem] transition-colors duration-150",
        active
          ? "bg-surface-2 text-ink"
          : "text-ink-tertiary hover:bg-surface-2/60 hover:text-ink-secondary",
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {children}
    </Link>
  );
}
