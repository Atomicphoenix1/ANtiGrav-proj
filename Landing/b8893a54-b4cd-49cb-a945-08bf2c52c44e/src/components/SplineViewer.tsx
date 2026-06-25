import { lazy, Suspense } from "react";
import { Loader2 } from "lucide-react";

// bundle-dynamic-imports: heavy 3D viewer loaded only when hero mounts
const Spline = lazy(() => import("@splinetool/react-spline"));

const SPLINE_URL =
  "https://prod.spline.design/eH5nyuI8badcW29P/scene.splinecode";

export function SplineViewer() {
  return (
    <div
      className="relative h-full w-full overflow-hidden rounded-2xl"
      aria-label="Interactive 3D scene"
    >
      <Suspense fallback={<SplineSkeleton />}>
        <Spline
          scene={SPLINE_URL}
          className="h-full w-full"
          style={{ background: "transparent" }}
        />
      </Suspense>
    </div>
  );
}

function SplineSkeleton() {
  return (
    <div className="flex h-full w-full items-center justify-center rounded-2xl bg-card/40">
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-accent" aria-hidden="true" />
        <span className="text-xs font-medium tracking-wide">Loading 3D scene…</span>
      </div>
    </div>
  );
}
