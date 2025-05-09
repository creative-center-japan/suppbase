'use client';

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

const videos = [
  "/videos/gym.mp4",
  "/videos/jog.mp4",
  "/videos/meal.mp4",
  "/videos/capsule.mp4",
  "/videos/protein.mp4"
];

export default function HomePage() {
  const [current, setCurrent] = useState(0);
  const [cycleCount, setCycleCount] = useState(0);
  const videoRefs = useRef<Array<HTMLVideoElement | null>>([]);

  useEffect(() => {
    if (cycleCount >= 1 && current === videos.length - 1) return;

    const interval = setInterval(() => {
      setCurrent((prev) => {
        const next = (prev + 1) % videos.length;
        if (next === 0) setCycleCount((c) => c + 1);
        return next;
      });
    }, 8000);

    return () => clearInterval(interval);
  }, [current, cycleCount]);

  useEffect(() => {
    const video = videoRefs.current[current];
    if (video) {
      video.currentTime = 0;
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise.catch((e) => {
          console.warn("Video play failed:", e.message);
        });
      }
    }
  }, [current]);

  return (
    <main className="relative overflow-hidden h-[70vh]">
      {/* 背景動画 */}
      {videos.map((src, index) => (
        <video
          key={src}
          ref={(el: HTMLVideoElement | null) => {
            videoRefs.current[index] = el;
          }}
          src={src}
          autoPlay
          muted
          playsInline
          loop={false}
          className={`absolute top-0 left-0 w-full h-full object-cover transition-opacity duration-1000 z-0 ${
            current === index ? "opacity-100" : "opacity-0"
          }`}
        />
      ))}

      {/* グラデーション境界ライン */}
      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-t from-white to-transparent z-10" />

      {/* コンテンツ（ロゴ・テキスト・ボタン） */}
      <div className="relative z-20 flex flex-col items-center justify-center h-full text-white text-center px-4 bg-black/30 backdrop-blur-sm">
        <h1 className="text-5xl font-extrabold drop-shadow-lg mb-4">SuppBase</h1>
        <p className="text-xl drop-shadow-md mb-8">サプリとデータで、ちょっと未来の自分へ。</p>

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
