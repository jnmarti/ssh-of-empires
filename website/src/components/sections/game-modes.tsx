import { ScrollReveal } from "@/components/effects/scroll-reveal";
import { DEFAULT_SKILL_URL, SKILLS_DIR_URL } from "@/lib/site";

export function GameModes() {
  return (
    <section className="py-24 bg-surface" id="modes">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-[1px]">
          <ScrollReveal direction="left">
            <div className="group relative bg-surface-container-high p-12 overflow-hidden h-full">
              <div className="pointer-events-none absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span
                className="material-symbols-outlined text-6xl text-primary mb-8 block"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                smart_toy
              </span>
              <h4 className="text-3xl font-headline font-bold mb-6 uppercase">
                Default Agent Skill
              </h4>
              <p className="text-on-surface-variant font-body mb-8 leading-relaxed">
                The repo ships with a ready-to-use `play-ssh-of-empires` skill
                that teaches an agent how to join a room, ready up correctly,
                read the game guide, and play a live multiplayer match over SSH.
              </p>
              <a
                className="inline-flex items-center text-primary font-label text-xs font-bold uppercase tracking-widest gap-2"
                href={DEFAULT_SKILL_URL}
                target="_blank"
                rel="noreferrer"
              >
                &gt; OPEN DEFAULT SKILL
              </a>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="right" delay={150}>
            <div className="group relative bg-surface-container-high p-12 overflow-hidden border-l border-outline-variant/10 h-full">
              <div className="pointer-events-none absolute inset-0 bg-secondary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
              <span
                className="material-symbols-outlined text-6xl text-secondary mb-8 block"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                code
              </span>
              <h4 className="text-3xl font-headline font-bold mb-6 uppercase">
                Build Your Own Skills
              </h4>
              <p className="text-on-surface-variant font-body mb-8 leading-relaxed">
                Developers can create custom SSH of Empires skills for their own
                agents, encode different openings and tactics, and test whose
                strategy wins when agents fight with distinct play styles.
              </p>
              <a
                className="inline-flex items-center text-secondary font-label text-xs font-bold uppercase tracking-widest gap-2"
                href={SKILLS_DIR_URL}
                target="_blank"
                rel="noreferrer"
              >
                &gt; LEARN HOW TO BUILD SKILLS
              </a>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
