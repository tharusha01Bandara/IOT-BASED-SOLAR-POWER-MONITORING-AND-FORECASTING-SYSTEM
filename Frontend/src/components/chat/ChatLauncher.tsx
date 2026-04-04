import { useLocation, useNavigate } from "react-router-dom";
import { MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ChatLauncher() {
  const navigate = useNavigate();
  const location = useLocation();

  if (location.pathname === "/chat") {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 md:bottom-6 md:right-6 z-40">
      <Button
        type="button"
        size="icon"
        className="h-12 w-12 rounded-full shadow-lg"
        onClick={() => navigate("/chat")}
        aria-label="Open AI chat"
      >
        <MessageSquare className="w-5 h-5" />
      </Button>
    </div>
  );
}
