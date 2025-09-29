import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  content: string
  className?: string
}

/**
 * MarkdownRenderer component
 * 
 * Renders markdown content with proper HTML formatting:
 * - **text** becomes <strong>text</strong>
 * - *text* becomes <em>text</em>
 * - Bullet points become proper <ul><li> lists
 * - Line breaks are preserved
 */
const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Customize heading rendering (no h1, h2 since we don't use ## or ###)
          h1: ({ node, ...props }) => <strong className="text-lg block mb-2" {...props} />,
          h2: ({ node, ...props }) => <strong className="text-base block mb-2" {...props} />,
          h3: ({ node, ...props }) => <strong className="text-base block mb-1" {...props} />,
          
          // Paragraphs with proper spacing
          p: ({ node, ...props }) => <p className="mb-3 leading-relaxed" {...props} />,
          
          // Strong (bold) text
          strong: ({ node, ...props }) => <strong className="font-semibold text-gray-900" {...props} />,
          
          // Emphasis (italic) text
          em: ({ node, ...props }) => <em className="italic" {...props} />,
          
          // Unordered lists (bullet points)
          ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-3 space-y-1" {...props} />,
          
          // Ordered lists
          ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-3 space-y-1" {...props} />,
          
          // List items
          li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
          
          // Links
          a: ({ node, ...props }) => (
            <a 
              className="text-green-600 hover:text-green-700 underline" 
              target="_blank" 
              rel="noopener noreferrer" 
              {...props} 
            />
          ),
          
          // Code blocks
          code: ({ node, inline, ...props }: any) => 
            inline ? (
              <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono" {...props} />
            ) : (
              <code className="block bg-gray-100 p-3 rounded text-sm font-mono overflow-x-auto mb-3" {...props} />
            ),
          
          // Blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic my-3" {...props} />
          ),
          
          // Tables
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto mb-3">
              <table className="min-w-full border-collapse border border-gray-300" {...props} />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th className="border border-gray-300 px-3 py-2 bg-gray-100 font-semibold text-left" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border border-gray-300 px-3 py-2" {...props} />
          ),
          
          // Horizontal rule
          hr: ({ node, ...props }) => <hr className="my-4 border-gray-300" {...props} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export default MarkdownRenderer

