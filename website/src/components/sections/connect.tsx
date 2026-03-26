import { ScrollReveal } from "@/components/effects/scroll-reveal";
import {
  GITHUB_URL,
  LLMS_URL,
  MULTIPLAYER_GUIDE_URL,
  README_URL,
  SSH_COMMAND,
} from "@/lib/site";

export function Connect() {
  return (
    <section
      className="py-24 bg-surface-container-low border-y border-outline-variant/10"
      id="play"
    >
      <div className="container mx-auto px-6 max-w-6xl">
        <ScrollReveal>
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-4xl font-headline font-bold mb-4 uppercase tracking-tight">
              Play SSH of Empires
            </h2>
            <p className="text-on-surface-variant font-body leading-relaxed">
              Jump into the public server, browse the repo, or hand the controls
              to a coding agent through the machine-readable guide.
            </p>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={150}>
          <div className="mt-12 max-w-4xl mx-auto">
            <div className="bg-surface-container-lowest p-8 border-l-4 border-primary text-left relative group">
              <div className="absolute top-4 right-4 text-[10px] font-label text-on-surface-variant uppercase">
                Public Server
              </div>
              <div className="font-mono text-lg md:text-xl text-on-surface break-all">
                <span className="text-secondary">$</span> {SSH_COMMAND}
                <span className="terminal-cursor text-primary" />
              </div>
              <p className="mt-4 text-sm text-on-surface-variant font-body">
                Best for players who want to join the live deployment immediately.
              </p>
            </div>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={300}>
          <div className="mt-10 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <a
              className="bg-surface-container-high p-5 border border-outline-variant/20 hover:border-primary transition-colors"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
            >
              <span className="block text-xs font-label uppercase tracking-widest text-primary mb-2">
                Source
              </span>
              <span className="block font-body font-bold">GitHub Repository</span>
            </a>
            <a
              className="bg-surface-container-high p-5 border border-outline-variant/20 hover:border-primary transition-colors"
              href={README_URL}
              target="_blank"
              rel="noreferrer"
            >
              <span className="block text-xs font-label uppercase tracking-widest text-primary mb-2">
                Docs
              </span>
              <span className="block font-body font-bold">README</span>
            </a>
            <a
              className="bg-surface-container-high p-5 border border-outline-variant/20 hover:border-primary transition-colors"
              href={LLMS_URL}
            >
              <span className="block text-xs font-label uppercase tracking-widest text-primary mb-2">
                Agents
              </span>
              <span className="block font-body font-bold">llms.txt</span>
            </a>
            <a
              className="bg-surface-container-high p-5 border border-outline-variant/20 hover:border-primary transition-colors"
              href={MULTIPLAYER_GUIDE_URL}
              target="_blank"
              rel="noreferrer"
            >
              <span className="block text-xs font-label uppercase tracking-widest text-primary mb-2">
                Multiplayer
              </span>
              <span className="block font-body font-bold">Room Guide</span>
            </a>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
