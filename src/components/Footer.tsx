export default function Footer() {
  return (
    <footer className="bg-white mt-12 text-center py-6 text-sm text-gray-500">
      <div className="max-w-screen-xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center">
        <p>© 2025 SuppBase. All rights reserved.</p>
        <div className="flex space-x-4 mt-2 sm:mt-0">
          <a href="https://twitter.com/" target="_blank" rel="noopener noreferrer">
            Twitter
          </a>
          <a href="https://instagram.com/" target="_blank" rel="noopener noreferrer">
            Instagram
          </a>
          <a href="mailto:contact@suppbase.com">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
