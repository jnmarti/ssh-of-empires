import {
  DEV_GUIDE_URL,
  GITHUB_URL,
  LLMS_URL,
  MULTIPLAYER_GUIDE_URL,
  README_URL,
} from "@/lib/site";

export function Footer() {
  return (
    <footer className="bg-surface-container-low border-t border-outline-variant/10 py-12 px-8 w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-7xl mx-auto">
        <div>
          <div className="text-lg font-bold text-primary mb-4 uppercase font-headline">
            SSH of Empires
          </div>
          <p className="text-outline-variant font-body text-xs uppercase tracking-widest leading-relaxed">
            A Real Time Strategy Game for your Terminal.
          </p>
        </div>

        <div className="flex flex-col gap-4">
          <h6 className="text-primary font-label text-[10px] uppercase tracking-[0.3em] mb-2">
            Docs
          </h6>
          <div className="flex flex-col gap-2">
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href={README_URL}
              target="_blank"
              rel="noreferrer"
            >
              &gt; README
            </a>
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href={MULTIPLAYER_GUIDE_URL}
              target="_blank"
              rel="noreferrer"
            >
              &gt; Multiplayer Guide
            </a>
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href={LLMS_URL}
            >
              &gt; llms.txt
            </a>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <h6 className="text-primary font-label text-[10px] uppercase tracking-[0.3em] mb-2">
            Project
          </h6>
          <div className="flex flex-col gap-2">
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
            >
              &gt; GitHub
            </a>
            <a
              className="text-outline-variant hover:text-primary font-body text-xs uppercase tracking-widest transition-all"
              href={DEV_GUIDE_URL}
              target="_blank"
              rel="noreferrer"
            >
              &gt; Developer Appendix
            </a>
            <p className="text-outline-variant font-body text-[10px] mt-4 opacity-50">
              &copy; {new Date().getFullYear()} Juan Martinez. All rights reserved.
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
