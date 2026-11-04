import type { ReactNode } from "react";

export default function Panel({ children, className = "", id, labelledBy }: {
  children: ReactNode;
  className?: string;
  id?: string;
  labelledBy?: string;
}) {
  return (
    <section id={id} aria-labelledby={labelledBy} className={`meteora-panel scroll-mt-6 rounded-meteora-card border border-meteora-border p-5 sm:p-6 ${className}`}>
      {children}
    </section>
  );
}
