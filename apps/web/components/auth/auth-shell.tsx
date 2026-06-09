import { Logo } from "@/components/brand/logo";

interface AuthShellProps {
  children: React.ReactNode;
}

export function AuthShell({ children }: AuthShellProps) {
  return (
    <div className="auth-page flex min-h-screen flex-col items-center justify-center px-5 py-10">
      <div className="mb-8">
        <Logo size="lg" href="/login" />
      </div>

      <div className="auth-form-card w-full max-w-[400px]">{children}</div>
    </div>
  );
}
