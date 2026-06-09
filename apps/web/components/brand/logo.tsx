import Link from "next/link";
import { cn } from "@/lib/utils";

const sizeMap = {
  xs: { img: 24, text: "text-sm" },
  sm: { img: 32, text: "text-base" },
  md: { img: 40, text: "text-lg" },
  lg: { img: 52, text: "text-xl" },
  xl: { img: 72, text: "text-2xl" },
} as const;

type LogoSize = keyof typeof sizeMap;

interface LogoProps {
  className?: string;
  imageClassName?: string;
  wordmarkClassName?: string;
  showWordmark?: boolean;
  size?: LogoSize;
  href?: string;
}

export function Logo({
  className,
  imageClassName,
  wordmarkClassName,
  showWordmark = true,
  size = "md",
  href,
}: LogoProps) {
  const { img, text } = sizeMap[size];

  const content = (
    <div className={cn("flex items-center gap-2.5", className)}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/KatalyzU.svg"
        alt="KatalyzU"
        width={img}
        height={img}
        className={cn("shrink-0 rounded-lg", imageClassName)}
      />
      {showWordmark && (
        <span className={cn("font-display font-bold tracking-tight", text, wordmarkClassName)}>
          KatalyzU
        </span>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex transition-opacity hover:opacity-90">
        {content}
      </Link>
    );
  }

  return content;
}
