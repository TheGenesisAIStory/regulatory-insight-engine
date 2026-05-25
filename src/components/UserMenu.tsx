import { LogOut, User as UserIcon } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useAuth, ROLE_LABELS } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const roleTone: Record<string, string> = {
  admin: "bg-primary/10 text-primary border-primary/25",
  senior_analyst: "bg-success/10 text-success border-success/25",
  analyst: "bg-secondary text-foreground border-border",
};

export const UserMenu = () => {
  const { profile, role, user, signOut } = useAuth();
  if (!user) return null;

  const name = profile?.full_name ?? user.email?.split("@")[0] ?? "Utente";
  const initials = name
    .split(" ")
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="flex items-center gap-2">
      {role && (
        <span
          className={cn(
            "hidden rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider sm:inline-flex",
            roleTone[role],
          )}
        >
          {ROLE_LABELS[role]}
        </span>
      )}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="h-8 gap-2 px-1.5">
            <Avatar className="h-7 w-7">
              <AvatarFallback className="bg-primary text-[11px] font-semibold text-primary-foreground">
                {initials || <UserIcon className="h-3.5 w-3.5" />}
              </AvatarFallback>
            </Avatar>
            <span className="hidden text-xs font-medium text-foreground md:inline">{name}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div className="flex flex-col">
              <span className="text-sm font-medium">{name}</span>
              <span className="text-[11px] font-normal text-muted-foreground">{user.email}</span>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          {role && (
            <DropdownMenuItem disabled className="text-xs">
              Ruolo: <span className="ml-1 font-medium">{ROLE_LABELS[role]}</span>
            </DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => signOut()} className="text-xs">
            <LogOut className="mr-2 h-3.5 w-3.5" /> Esci
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
