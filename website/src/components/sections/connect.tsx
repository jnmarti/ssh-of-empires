import { ScrollReveal } from "@/components/effects/scroll-reveal";

export function Connect() {
  return (
    <section className="py-24 bg-surface-container-low border-y border-outline-variant/10">
      <div className="container mx-auto px-6 text-center max-w-4xl">
        <ScrollReveal>
          <h2 className="text-4xl font-headline font-bold mb-12 uppercase tracking-tight">
            Initiate Connection
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={150}>
          <div className="bg-surface-container-lowest p-8 border-l-4 border-primary text-left relative group">
            <div className="absolute top-4 right-4 text-[10px] font-label text-on-surface-variant uppercase">
              Command Line Interface
            </div>
            <div className="font-mono text-xl md:text-2xl text-on-surface">
              <span className="text-secondary">$</span> ssh
              play.sshofempires.com{" "}
              <span className="terminal-cursor text-primary" />
            </div>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={300}>
          <div className="mt-8 flex flex-wrap justify-center gap-12">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-primary text-3xl">
                lock
              </span>
              <div className="text-left">
                <span className="block text-xs font-label uppercase tracking-widest text-on-surface-variant">
                  Security
                </span>
                <span className="block font-body text-sm font-bold">
                  RSA-4096 Encrypted
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-secondary text-3xl">
                bolt
              </span>
              <div className="text-left">
                <span className="block text-xs font-label uppercase tracking-widest text-on-surface-variant">
                  Performance
                </span>
                <span className="block font-body text-sm font-bold">
                  Real-time Sync
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-tertiary text-3xl">
                public
              </span>
              <div className="text-left">
                <span className="block text-xs font-label uppercase tracking-widest text-on-surface-variant">
                  Availability
                </span>
                <span className="block font-body text-sm font-bold">
                  Global Clusters
                </span>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
