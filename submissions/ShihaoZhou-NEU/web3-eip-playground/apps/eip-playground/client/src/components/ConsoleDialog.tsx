import { useState, useEffect, useRef } from "react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Terminal, Send, X } from "lucide-react";

interface Message {
  role: "tutor" | "user";
  text: string;
}

interface ConsoleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  messages: Message[];
  onSubmit: (answer: string) => void;
  isLoading: boolean;
}

export default function ConsoleDialog({
  open,
  onOpenChange,
  messages,
  onSubmit,
  isLoading,
}: ConsoleDialogProps) {
  const [input, setInput] = useState("");
  const [displayedMessages, setDisplayedMessages] = useState<
    Array<{ role: "tutor" | "user"; text: string; isComplete: boolean }>
  >([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 苹果系统字体栈
  const appleFontStack = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Helvetica, Arial, sans-serif';

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayedMessages]);

  useEffect(() => {
    if (open) {
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  }, [open]);

  useEffect(() => {
    if (messages.length === 0) {
      setDisplayedMessages([]);
      return;
    }

    const lastMessage = messages[messages.length - 1];
    const lastDisplayed = displayedMessages[displayedMessages.length - 1];

    if (
      !lastDisplayed ||
      messages.length > displayedMessages.length ||
      lastMessage.text !== lastDisplayed.text
    ) {
      const previousMessages = messages.slice(0, -1).map(msg => ({
        ...msg,
        isComplete: true,
      }));

      if (lastMessage.role === "user") {
        setDisplayedMessages([
          ...previousMessages,
          { ...lastMessage, isComplete: true },
        ]);
        return;
      }

      setDisplayedMessages([
        ...previousMessages,
        { ...lastMessage, text: "", isComplete: false },
      ]);

      const words = lastMessage.text.split(" ");
      let currentWordIndex = 0;

      const typewriterInterval = setInterval(() => {
        if (currentWordIndex < words.length) {
          setDisplayedMessages(prev => {
            const newMessages = [...prev];
            const lastIdx = newMessages.length - 1;
            const currentText = newMessages[lastIdx].text;
            const nextWord = words[currentWordIndex];
            newMessages[lastIdx] = {
              ...newMessages[lastIdx],
              text: currentText ? `${currentText} ${nextWord}` : nextWord,
              isComplete: currentWordIndex === words.length - 1,
            };
            return newMessages;
          });
          currentWordIndex++;
        } else {
          clearInterval(typewriterInterval);
        }
      }, 50); // 稍微加快了打字机速度以适应现代字体

      return () => clearInterval(typewriterInterval);
    }
  }, [messages]);

  const handleSubmit = () => {
    if (input.trim() && !isLoading) {
      onSubmit(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} modal>
      <DialogContent 
        /* 1. 宽度放大(max-w-[1100px])，高度缩小(h-[75vh])，比例更优美 */
        /* 4. 整体字体改为苹果系统字体 */
        className="!max-w-none w-[80vw] max-w-[1100px] h-[75vh] bg-black/95 border-2 border-green-500/50 p-0 overflow-hidden flex flex-col [&>button]:hidden"
        style={{ fontFamily: appleFontStack }}
        onPointerDownOutside={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
      >
        {/* Header */}
        <div className="bg-green-900/30 border-b border-green-500/50 px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-5 h-5 text-green-400" />
            <span className="text-green-400 font-semibold tracking-tight font-pixel">
              ERC-8004 KNOWLEDGE CHALLENGE
            </span>
          </div>

          <div className="flex items-center">
            {/* 2. 这里的按钮替代了默认关闭按钮，3. 移除了黄色和绿色小圆点 */}
            <button
              onClick={() => onOpenChange(false)}
              className="w-7 h-7 rounded-md hover:bg-red-500/20 flex items-center justify-center transition-all group"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5 text-green-500/50 group-hover:text-red-500" />
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-8 space-y-6 custom-scrollbar">
          {displayedMessages.map((msg, idx) => (
            <div key={idx} className="space-y-2">
              <div className="flex items-center gap-2 opacity-70">
                <span className="text-green-500 font-medium text-xs tracking-wider font-pixel">
                  {msg.role === "tutor" ? "TUTOR@ERC-8004" : "USER@TERMINAL"}
                </span>
                <span className="text-green-600 font-pixel">$</span>
              </div>

              {/* 4. 消息内容字体已通过父级应用为苹果系统字体 */}
              <div
                className={`pl-0 whitespace-pre-wrap text-[15px] leading-relaxed font-normal ${
                  msg.role === "tutor" ? "text-green-100" : "text-cyan-200"
                }`}
              >
                {msg.text}
                {msg.role === "tutor" && !msg.isComplete && (
                  <span className="inline-block w-1.5 h-4 bg-green-400 ml-1 animate-pulse align-middle"></span>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex items-center gap-2 text-green-400/80 animate-pulse pt-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span className="text-sm font-medium font-pixel">Analyzing response...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-green-500/30 p-6 bg-black/40">
          <div className="flex items-center gap-2 mb-3 opacity-50">
            <span className="text-green-500 text-xs font-bold font-pixel">INPUT_COMMAND</span>
            <div className="h-[1px] flex-1 bg-green-500/20"></div>
          </div>

          <div className="relative group">
            {/* 4. 输入框内文字字体改为苹果系统字体 */}
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Enter your answer here..."
              className="w-full bg-black/60 border-green-500/20 text-green-100 resize-none focus:border-green-500/50 placeholder:text-green-900/50 min-h-[80px] max-h-[200px] overflow-y-auto text-[15px] p-4 transition-all custom-scrollbar"
            //   className="w-full bg-black/60 border-green-500/20 text-green-100 resize-none focus:border-green-500/50 placeholder:text-green-900/50 min-h-[80px] text-[15px] p-4 transition-all"
              style={{ fontFamily: appleFontStack }}
            />
            
            <div className="absolute bottom-3 right-3 flex items-center gap-4">
               {/* <span className="text-[10px] text-green-900 font-medium hidden sm:inline font-pixel">
                PRESS ENTER TO EXECUTE
              </span> */}
              <Button
                onClick={handleSubmit}
                disabled={!input.trim() || isLoading}
                className="bg-green-600/90 hover:bg-green-500 text-black font-bold border-none h-9 px-4"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
        <style dangerouslySetInnerHTML={{ __html: `
          .custom-scrollbar::-webkit-scrollbar {
            width: 6px;
          }
          .custom-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(34, 197, 94, 0.3);
            border-radius: 10px;
          }
          .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: rgba(34, 197, 94, 0.8);
          }
        `}} />
      </DialogContent>
    </Dialog>
  );
}