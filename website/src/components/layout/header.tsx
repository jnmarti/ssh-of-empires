"use client";

import { useState } from "react";
import { GITHUB_URL } from "@/lib/site";

const navLinks = [
  { label: "The Game", href: "#game" },
  { label: "Humans + Agents", href: "#agents" },
  { label: "Play", href: "#play" },
  { label: "Field Guide", href: "#field-guide" },
];

export function Header() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 z-50 w-full px-6 py-4 bg-[#0e0e0e] border-b border-outline-variant/20 flex justify-between items-center">
      <div className="text-2xl font-black uppercase tracking-tighter text-primary font-headline">
        SSH of Empires
      </div>

      <div className="hidden md:flex items-center space-x-8">
        {navLinks.map((link) => (
          <a
            key={link.label}
            href={link.href}
            className="font-label uppercase tracking-widest text-xs transition-colors duration-200 text-outline-variant hover:text-primary"
          >
            {link.label}
          </a>
        ))}
      </div>

      <div className="flex items-center gap-4">
        <a
          className="hidden sm:inline-flex border border-primary/30 text-primary px-4 py-2 font-label text-xs font-bold uppercase tracking-widest transition-all hover:bg-primary/10"
          href={GITHUB_URL}
          target="_blank"
          rel="noreferrer"
        >
          GitHub
        </a>
        <a
          className="bg-primary hover:bg-primary-dim text-on-primary px-4 py-2 font-label text-xs font-bold uppercase tracking-widest transition-all"
          href="#play"
        >
          Play via SSH
        </a>

        <button
          className="md:hidden text-on-surface"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          <span className="material-symbols-outlined text-2xl">
            {open ? "close" : "menu"}
          </span>
        </button>
      </div>

      {open && (
        <div className="absolute top-full left-0 w-full bg-surface-container border-b border-outline-variant/20 md:hidden">
          <div className="flex flex-col p-6 gap-4">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setOpen(false)}
                className="font-label uppercase tracking-widest text-xs py-2 text-outline-variant"
              >
                {link.label}
              </a>
            ))}
            <a
              className="font-label uppercase tracking-widest text-xs py-2 text-outline-variant"
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              onClick={() => setOpen(false)}
            >
              GitHub
            </a>
          </div>
        </div>
      )}
    </nav>
  );
}
