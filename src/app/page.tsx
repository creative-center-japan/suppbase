// healthy-site/src/app/page.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';

const videos = [
  '/videos/gym.mp4',
  '/videos/jog.mp4',
  '/videos/meal.mp4',
  '/videos/capsule.mp4',
  '/videos/protein.mp4',
];

// 次クリップを早めに再生してからフェード（ms）
const PREPARE_MS = 300;
// メタデータ未取得時の保険長さ（ms）
const MIN_DURATION = 3000;

export default function HomePage() {
  const [current, setCurrent] = useState(0);
  const [durations, setDurations] = useState<number[]>(
    Array(videos.length).fill(NaN)
  );
  const [cycleCount, setCycleCount] = useState(0);

  const videoRefs = useRef<Array<HTMLVideoElement | null>>([]);
  const timerRef = useRef<number | null>(null);

  // すべて事前ロード
  useEffect(() => {
    videoRefs.current.forEach((v) => {
      if (v) {
        v.preload = 'auto';
        try {
          v.load();
        } catch {
          /* noop */
        }
      }
    });
  }, []);

  // メタデータから実長を記録
  const handleLoadedMetadata = (i: number) => {
    const v = videoRefs.current[i];
    if (v && !Number.isNaN(v.duration)) {
      setDurations((d) => {
        const cp = d.slice();
        cp[i] = v.duration * 1000; // ms
        return cp;
      });
    }
  };

  // 現在の動画を再生し、次をプリロールしてからインデックス切替
  useEffect(() => {
    const curEl = videoRefs.current[current];
    if (!curEl) return;

    curEl.currentTime = 0;
    curEl.muted = true;
    curEl.play().catch(() => {});

    const next = (current + 1) % videos.length;
    const nextEl = videoRefs.current[next];

    const durationMs = Number.isNaN(durations[current])
      ? MIN_DURATION
      : durations[current];
    const fireAt = Math.max(0, durationMs - PREPARE_MS);

    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    // 切替直前に次を見えない状態で再生開始（デコードを走らせる）
    timerRef.current = window.setTimeout(() => {
      if (nextEl) {
        nextEl.currentTime = 0;
        nextEl.muted = true;
        nextEl.play().catch(() => {});
      }
      // ほんの少し待ってからフェード切替
      window.setTimeout(() => {
        setCurrent(next);
        if (next === 0) setCycleCount((c) => c + 1);
      }, 50);
    }, fireAt);

    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [current, durations]);

  // ref コールバック（値を返さない！）
  const setVideoRef = (i: number) => (el: HTMLVideoElement | null) => {
    videoRefs.current[i] = el;
  };

  return (
    <main className="relative overflow-hidden h-[70vh] bg-black">
      {videos.map((src, index) => (
        <video
          key={src}
          ref={setVideoRef(index)}
          src={src}
          muted
          playsInline
          preload="auto"
          loop={false}
          onLoadedMetadata={() => handleLoadedMetadata(index)}
          className={`absolute top-0 left-0 w-full h-full object-cover transition-opacity duration-500 z-0 ${
            current === index ? 'opacity-100' : 'opacity-0'
          }`}
        />
      ))}

      {/* 下部の黒→透明グラデ */}
      <div className="absolute bottom-0 left-0 w-full h-16 bg-gradient-to-t from-black to-transparent z-10" />

      {/* 中央オーバーレイ（やや濃い目） */}
      <div className="relative z-20 flex flex-col items-center justify-center h-full text-white text-center px-4 bg-black/40 backdrop-blur-sm">
        <h1 className="text-5xl font-extrabold drop-shadow-lg mb-4">SuppBase</h1>
        <p className="text-xl drop-shadow-md mb-8">
          サプリとデータで、ちょっと未来の自分へ。
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/rankings/japan"
            className="bg-green-600 px-6 py-3 rounded-md hover:bg-green-700 transition"
          >
            ランキングを見る →
          </Link>
          <Link
            href="/blog"
            className="bg-white text-green-700 px-6 py-3 rounded-md hover:bg-gray-100 transition"
          >
            ブログを読む →
          </Link>
        </div>
      </div>
    </main>
  );
}
