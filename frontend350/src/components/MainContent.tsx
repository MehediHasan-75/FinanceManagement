import React from "react";
import ChatArea from "./ChatArea";

const MainContent = ({ showChat }: { showChat: boolean }) => {
  return (
    <div className={`flex text-center h-[100vh] flex-1 w-full bg-amber-200`}>
      {showChat ? (
        <>
          <div className="w-3/5 pt-[10vh]">MainContent</div>
          <div className="w-2/5">
            <ChatArea />
          </div>
        </>
      ) : (
        <div className="w-full pt-[10vh]">MainContent</div>
      )}
    </div>
  );
};

export default MainContent;
