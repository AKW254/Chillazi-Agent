// components/AboutCard.tsx
import type { ReactNode } from "react";

type AboutCardProps = {
  /** The image source (URL or import) */
  imageSrc: string;
  /** Alt text for the image */
  imageAlt: string;
  /** Card heading (e.g. "About Chillazi") */
  title: string;
  /** Main body content (can be a string or JSX for rich text) */
  children: ReactNode;
  /** Optional image position – defaults to left on desktop */
  imagePosition?: "left" | "right";
};

export function AboutCard({
  imageSrc,
  imageAlt,
  title,
  children,
  imagePosition = "left",
}: AboutCardProps) {
  const isImageLeft = imagePosition === "left";

  return (
    <div
      className={`flex flex-col gap-10 overflow-hidden rounded-3xl border border-sand-200 bg-sand-50/70 shadow-lg backdrop-blur md:flex-row ${
        isImageLeft ? "" : "md:flex-row-reverse"
      }`}
    >
      {/* Image side */}
      <div className="relative w-full md:w-1/2">
        <img
          src={imageSrc}
          alt={imageAlt}
          className="h-64 w-full object-cover md:h-full"
          loading="lazy"
        />
        {/* Subtle gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-sand-50/30 to-transparent md:bg-gradient-to-r" />
      </div>

      {/* Content side */}
      <div className="flex flex-col justify-center px-8 py-8 md:w-1/2 md:px-12 md:py-12">
        <h2 className="font-display text-3xl italic text-espresso-900 md:text-4xl">
          {title}
        </h2>
        <div className="mt-5 space-y-4 text-espresso-900/80 leading-relaxed">
          {children}
        </div>
        {/* Optional CTA – can be passed via children or added here */}
      </div>
    </div>
  );
}
