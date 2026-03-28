import type { PropsWithChildren, ReactNode } from "react";

type CardProps = PropsWithChildren<{
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
}>;

export function Card({ title, subtitle, actions, className, children }: CardProps) {
  return (
    <section className={`card ${className ?? ""}`.trim()}>
      {(title || subtitle || actions) && (
        <div className="card-header">
          <div>
            {title ? <h3>{title}</h3> : null}
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          {actions ? <div>{actions}</div> : null}
        </div>
      )}
      {children}
    </section>
  );
}

export function Button({
  children,
  onClick,
  variant = "primary",
  disabled = false,
}: PropsWithChildren<{
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  disabled?: boolean;
}>) {
  return (
    <button type="button" className={`button ${variant}`} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: PropsWithChildren<{ tone?: "positive" | "warning" | "negative" | "neutral" }>) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
