import { useEffect } from "react";

interface AdBannerProps {
  slot: string;
  format?: string;
  className?: string;
}

const AD_CLIENT = "ca-pub-4007596710868693";

export function AdBanner({ slot, format = "auto", className }: AdBannerProps) {
  useEffect(() => {
    try {
      // @ts-expect-error adsbygoogle is injected by the AdSense script
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      // Silently ignore — ad blocker or script not yet loaded
    }
  }, []);

  return (
    <div className={className}>
      <ins
        className="adsbygoogle"
        style={{ display: "block" }}
        data-ad-client={AD_CLIENT}
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive="true"
      />
    </div>
  );
}
