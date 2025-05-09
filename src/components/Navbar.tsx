'use client';

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/rankings/overseas", label: "Overseas" },
  { href: "/blog", label: "Blog" },
  { href: "/about", label: "About" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [isJapanOpen, setJapanOpen] = useState(false);

  return (
    <nav className="bg-white shadow-md px-6 py-4 sticky top-0 z-50">
      <div className="max-w-screen-xl mx-auto flex items-center justify-between">
        {/* ロゴ＋タイトル */}
        <Link href="/" className="flex flex-col leading-tight">
          <div className="flex items-center space-x-2">
            <Image src="/suppbase-logo.png" alt="SuppBase logo" width={32} height={32} />
            <span className="text-2xl font-bold text-green-700">SuppBase</span>
          </div>
        </Link>

        {/* ハンバーガーアイコン（スマホ用） */}
        <button
          className="sm:hidden text-gray-700"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          ☰
        </button>

        {/* 通常ナビゲーション（PC用） */}
        <div className="hidden sm:flex space-x-6 text-sm font-medium items-center">
          {/* Japanランキング with dropdown */}
          <div className="relative">
            <button
              onClick={() => setJapanOpen(!isJapanOpen)}
              className={`hover:text-green-700 transition ${
                pathname.startsWith('/rankings/japan')
                  ? "text-green-700 font-semibold underline underline-offset-4"
                  : "text-gray-700"
              }`}
            >
              Japanランキング ▾
            </button>
            {isJapanOpen && (
              <div className="absolute bg-white border rounded shadow-md mt-2 w-48 z-50">
                <ul className="text-sm text-gray-700">
                  <li><Link href="/rankings/japan/protein" onClick={() => setJapanOpen(false)} className={`block px-4 py-2 hover:bg-gray-100 ${pathname === '/rankings/japan/protein' ? 'bg-green-100 font-bold' : ''}`}>プロテイン</Link></li>
                  <li><Link href="/rankings/japan/supplements" onClick={() => setJapanOpen(false)} className={`block px-4 py-2 hover:bg-gray-100 ${pathname === '/rankings/japan/supplements' ? 'bg-green-100 font-bold' : ''}`}>サプリメント</Link></li>
                  <li><Link href="/rankings/japan/foods" onClick={() => setJapanOpen(false)} className={`block px-4 py-2 hover:bg-gray-100 ${pathname === '/rankings/japan/foods' ? 'bg-green-100 font-bold' : ''}`}>フード</Link></li>
                  <li><Link href="/rankings/japan/others" onClick={() => setJapanOpen(false)} className={`block px-4 py-2 hover:bg-gray-100 ${pathname === '/rankings/japan/others' ? 'bg-green-100 font-bold' : ''}`}>その他</Link></li>
                </ul>
              </div>
            )}
          </div>

          {/* その他のリンク */}
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`hover:text-green-700 transition ${
                pathname.startsWith(link.href)
                  ? "text-green-700 font-semibold underline underline-offset-4"
                  : "text-gray-700"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>

      {/* モバイルメニュー（開閉式） */}
      {menuOpen && (
        <div className="sm:hidden mt-4 space-y-2 text-sm text-center font-medium">
          <div className="text-gray-700 font-semibold">Japanランキング</div>
          <Link href="/rankings/japan/protein" onClick={() => setMenuOpen(false)} className="block py-2 hover:text-green-700">└ プロテイン</Link>
          <Link href="/rankings/japan/supplements" onClick={() => setMenuOpen(false)} className="block py-2 hover:text-green-700">└ サプリメント</Link>
          <Link href="/rankings/japan/foods" onClick={() => setMenuOpen(false)} className="block py-2 hover:text-green-700">└ フード</Link>
          <Link href="/rankings/japan/others" onClick={() => setMenuOpen(false)} className="block py-2 hover:text-green-700">└ その他</Link>

          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMenuOpen(false)}
              className={`block py-2 hover:text-green-700 ${
                pathname.startsWith(link.href)
                  ? "text-green-700 font-semibold underline underline-offset-4"
                  : "text-gray-700"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
