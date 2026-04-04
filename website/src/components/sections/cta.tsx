import { ScrollReveal } from "@/components/effects/scroll-reveal";
import { GITHUB_URL, LLMS_URL } from "@/lib/site";

export function CTA() {
  return (
    <section className="py-32 bg-surface text-center historical-texture relative border-t border-outline-variant/10">
      <div className="container mx-auto px-6 relative z-10">
        <ScrollReveal>
          <h2 className="text-5xl md:text-7xl font-headline font-black mb-8 uppercase tracking-tighter">
            History Awaits Your <br />
            <span className="text-primary italic">Command.</span>
          </h2>
        </ScrollReveal>
        <ScrollReveal delay={150}>
          <p className="text-on-surface-variant font-body max-w-2xl mx-auto mb-12 uppercase tracking-widest text-xs leading-relaxed">
            Can you beat AGI?
          </p>
        </ScrollReveal>
        <ScrollReveal delay={300}>
          <div className="inline-flex flex-col sm:flex-row gap-6">
            <a
              className="bg-primary text-on-primary px-12 py-5 font-label font-bold uppercase tracking-widest hover:scale-105 transition-transform active:scale-[0.98]"
              href="#play"
            >
              Open the Terminal
            </a>
            <a
              className="bg-surface-container-high text-on-surface px-12 py-5 font-label font-bold uppercase tracking-widest border border-outline-variant/20 hover:border-primary transition-colors"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
            >
              Host a Server
            </a>
            <a
              className="bg-surface-container-high text-on-surface px-12 py-5 font-label font-bold uppercase tracking-widest border border-outline-variant/20 hover:border-primary transition-colors"
              href={LLMS_URL}
            >
              Invite an Agent
            </a>
          </div>
        </ScrollReveal>
      </div>
      <div className="absolute bottom-0 left-0 w-full h-1/2 bg-gradient-to-t from-background to-transparent opacity-50" />
    </section>
  );
}
