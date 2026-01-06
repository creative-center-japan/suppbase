'use client';

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [isJapanOpen, setJapanOpen] = useState(false);
  const [isOverseasOpen, setOverseasOpen] = useState(false);

  const jpWrapRef = useRef<HTMLDivElement | null>(null);
  const osWrapRef = useRef<HTMLDivElement | null>(null);

  // 外側クリック & Esc
  useEffect(() => {
    const handleDown = (e: MouseEvent | TouchEvent) => {
      if (
        (jpWrapRef.current && e.target instanceof Node && !jpWrapRef.current.contains(e.target)) &&
        (osWrapRef.current && e.target instanceof Node && !osWrapRef.current.contains(e.target))
      ) {
        setJapanOpen(false);
        setOverseasOpen(false);
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setJapanOpen(false);
        setOverseasOpen(false);
      }
    };
    document.addEventListener("mousedown", handleDown);
    document.addEventListener("touchstart", handleDown);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleDown);
      document.removeEventListener("touchstart", handleDown);
      document.removeEventListener("keydown", handleEsc);
    };
  }, []);

  useEffect(() => {
    setJapanOpen(false);
    setOverseasOpen(false);
    setMenuOpen(false);
  }, [pathname]);

  return (
    <nav className="bg-white shadow-md px-6 py-4 sticky top-0 z-50">
      <div className="max-w-screen-xl mx-auto flex items-center justify-between">
        {/* ロゴ */}
        <Link href="/" className="flex items-center space-x-2">
          <Image src="/suppbase-logo.png" alt="SuppBase logo" width={32} height={32} />
          <span className="text-2xl font-bold text-green-700">SuppBase</span>
        </Link>

        {/* ハンバーガー */}
        <button
          className="sm:hidden text-gray-700"
          onClick={() => setMenuOpen(v => !v)}
        >
          ☰
        </button>

        {/* PCナビ */}
        <div className="hidden sm:flex space-x-6 text-sm font-medium items-center">
          {/* Japanランキング */}
          <div className="relative" ref={jpWrapRef}>
            <button
              onClick={() => setJapanOpen(v => !v)}
              className={`hover:text-green-700 ${
                pathname.startsWith('/rankings/japan')
                  ? "text-green-700 font-semibold underline underline-offset-4"
                  : "text-gray-700"
              }`}
            >
              Japanランキング ▾
            </button>

            {isJapanOpen && (
              <div className="absolute right-0 bg-white border rounded shadow-md mt-2 w-48 z-50">
                <Link href="/rankings/japan/protein" className="block px-4 py-2 hover:bg-gray-100">プロテイン</Link>
                <Link href="/rankings/japan/supplements" className="block px-4 py-2 hover:bg-gray-100">サプリメント</Link>
              </div>
            )}
          </div>

          {/* 海外ランキング */}
          <div className="relative" ref={osWrapRef}>
            <button
              onClick={() => setOverseasOpen(v => !v)}
              className="hover:text-green-700 text-gray-700"
            >
              海外ランキング ▾
            </button>

            {isOverseasOpen && (
              <div className="absolute right-0 bg-white border rounded shadow-md mt-2 w-48 z-50">
                <Link href="/rankings/overseas/us" className="block px-4 py-2 hover:bg-gray-100">アメリカ</Link>
                <Link href="/rankings/overseas/uk" className="block px-4 py-2 hover:bg-gray-100">イギリス</Link>
              </div>
            )}
          </div>

          <Link href="/blog" className="hover:text-green-700 text-gray-700">Blog</Link>
          <Link href="/about" className="hover:text-green-700 text-gray-700">About</Link>
        </div>
      </div>

      {/* モバイル */}
      {menuOpen && (
        <div className="sm:hidden mt-4 space-y-2 text-sm text-center font-medium">
          <div>Japanランキング</div>
          <Link href="/rankings/japan/protein" className="block">└ プロテイン</Link>
          <Link href="/rankings/japan/supplements" className="block">└ サプリメント</Link>

          <div className="mt-4">海外ランキング</div>
          <Link href="/rankings/overseas/us" className="block">└ アメリカ</Link>
          <Link href="/rankings/overseas/uk" className="block">└ イギリス</Link>

          <Link href="/blog" className="block">Blog</Link>
          <Link href="/about" className="block">About</Link>
        </div>
      )}
    </nav>
  );
}
