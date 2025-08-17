import React, { useEffect, useRef, useState } from "react";
import "./App.css";

function App() {
  const [nickname, setNickname] = useState("");
  const [inputNickname, setInputNickname] = useState("");
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");
  const [isLoading, setIsLoading] = useState(false);
  
  const ws = useRef(null);
  const messagesEndRef = useRef(null);

  // 메시지 히스토리 가져오기
  const fetchMessages = async () => {
    try {
      const res = await fetch('http://localhost:8000/messages');
      const data = await res.json();
      setChatLog(data);
    } catch (error) {
      console.error('메시지 로드 실패:', error);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  useEffect(() => {
    if (nickname && !ws.current) {
      connectWebSocket();
    }
  }, [nickname]);

  const connectWebSocket = () => {
    if (!nickname) return;
    
    ws.current = new WebSocket(`ws://localhost:8000/ws/${nickname}`);
    
    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket 연결됨');
    };
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket 메시지 수신:', data);
        
        // AI 응답이나 시스템 메시지인 경우 즉시 채팅창에 추가
        if (data.type === 'ai_chat' || data.type === 'function_result' || 
            data.type === 'image' || data.type === 'error' || data.type === 'system') {
          setChatLog((prev) => [...prev, data]);
        } else {
          // 일반 메시지도 추가 (중복 방지)
          setChatLog((prev) => {
            // 같은 timestamp와 message가 있는지 확인
            const isDuplicate = prev.some(msg => 
              msg.timestamp === data.timestamp && 
              msg.message === data.message &&
              msg.nickname === data.nickname
            );
            
            if (!isDuplicate) {
              return [...prev, data];
            }
            return prev;
          });
        }
      } catch (e) {
        console.error("잘못된 메시지 형식:", event.data);
      }
    };
    
    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket 연결 끊어짐');
      ws.current = null;
      
      // 자동 재연결 (3초 후)
      if (nickname) {
        setTimeout(() => {
          console.log('자동 재연결 시도...');
          connectWebSocket();
        }, 3000);
      }
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      setIsConnected('연결 오류');
    };
  };

  // 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  // 일반 메시지 전송
  const sendMessage = () => {
    if (!message.trim() || !nickname.trim()) return;

    const payload = {
      type: "text",
      nickname,
      message: message,
      timestamp: new Date().toISOString(),
    };

    ws.current?.send(JSON.stringify(payload));
    setMessage("");
  };

  // AI 챗봇 요청
  const sendAIChat = () => {
    if (!message.trim() || !nickname.trim()) return;

    // 사용자 질문을 즉시 채팅창에 추가
    const userMessage = {
      type: "text",
      nickname,
      message: message,
      timestamp: new Date().toISOString(),
    };
    
    setChatLog(prev => [...prev, userMessage]);

    const payload = {
      type: "ai_chat",
      nickname,
      message: message,
      timestamp: new Date().toISOString(),
    };

    ws.current?.send(JSON.stringify(payload));
    setMessage("");
  };

  // Function Calling 요청
  const sendFunctionCall = () => {
    if (!message.trim() || !nickname.trim()) return;

    // 사용자 질문을 즉시 채팅창에 추가
    const userMessage = {
      type: "text",
      nickname,
      message: message,
      timestamp: new Date().toISOString(),
    };
    
    setChatLog(prev => [...prev, userMessage]);

    const payload = {
      type: "function_call",
      nickname,
      message: message,
      timestamp: new Date().toISOString(),
    };

    ws.current?.send(JSON.stringify(payload));
    setMessage("");
  };

  // 이미지 생성 요청
  const generateImage = () => {
    if (!message.trim() || !nickname.trim()) return;

    // 사용자 요청을 즉시 채팅창에 추가
    const userMessage = {
      type: "text",
      nickname,
      message: `이미지 생성 요청: ${message}`,
      timestamp: new Date().toISOString(),
    };
    
    setChatLog(prev => [...prev, userMessage]);

    const payload = {
      type: "image_generation",
      nickname,
      message: message,
      timestamp: new Date().toISOString(),
    };

    ws.current?.send(JSON.stringify(payload));
    setMessage("");
  };

  // REST API 호출 함수들
  const callSpellCheck = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/spellcheck', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: message }),
      });
      const result = await response.json();
      
      const systemMessage = {
        type: "system",
        nickname: "맞춤법 검사기",
        message: `원본: ${result.original}\n교정: ${result.corrected}`,
        timestamp: new Date().toISOString(),
      };
      
      setChatLog(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error('맞춤법 검사 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const callTranslate = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: message }),
      });
      const result = await response.json();
      
      const systemMessage = {
        type: "system",
        nickname: "번역기",
        message: `원본: ${result.original}\n번역: ${result.translated}`,
        timestamp: new Date().toISOString(),
      };
      
      setChatLog(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error('번역 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const callWeather = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/weather', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ location: message }),
      });
      const result = await response.json();
      
      const systemMessage = {
        type: "system",
        nickname: "날씨 봇",
        message: `${result.location}: ${result.temperature}, ${result.condition}, 습도 ${result.humidity}, 바람 ${result.wind}`,
        timestamp: new Date().toISOString(),
      };
      
      setChatLog(prev => [...prev, systemMessage]);
    } catch (error) {
      console.error('날씨 정보 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const callTTS = async () => {
    if (!message.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/tts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: message }),
      });
      const result = await response.json();
      
      if (result.audio_base64) {
        // 오디오 재생
        const audio = new Audio(`data:audio/mp3;base64,${result.audio_base64}`);
        audio.play();
        
        const systemMessage = {
          type: "system",
          nickname: "TTS",
          message: `음성 변환 완료: ${result.text}`,
          timestamp: new Date().toISOString(),
        };
        
        setChatLog(prev => [...prev, systemMessage]);
      }
    } catch (error) {
      console.error('TTS 실패:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNicknameSet = () => {
    if (inputNickname.trim()) {
      setNickname(inputNickname.trim());
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (activeTab === "chat") {
        sendMessage();
      } else if (activeTab === "ai") {
        sendAIChat();
      } else if (activeTab === "function") {
        sendFunctionCall();
      } else if (activeTab === "image") {
        generateImage();
      }
    }
  };

  const renderMessage = (msgObj, i) => {
    const isSystem = msgObj.type === "system";
    const isAI = msgObj.nickname === "AI 어시스턴트";
    const isImage = msgObj.type === "image";
    const isError = msgObj.type === "error";
    
    return (
      <div key={i} className={`message ${isSystem ? 'system' : ''} ${isAI ? 'ai' : ''} ${isError ? 'error' : ''}`}>
        <div className="message-header">
          <strong>{msgObj.nickname}</strong>
          <span className="timestamp">
            {new Date(msgObj.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className="message-content">
          {isImage && msgObj.image_data ? (
            <div>
              <p>{msgObj.message}</p>
              <img 
                src={`data:image/png;base64,${msgObj.image_data}`} 
                alt="Generated" 
                className="generated-image"
              />
            </div>
          ) : (
            <p>{msgObj.message}</p>
          )}
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "chat":
        return (
          <div className="input-section">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              disabled={!isConnected}
            />
            <button onClick={sendMessage} disabled={!isConnected || !message.trim()}>
              전송
            </button>
          </div>
        );
      case "ai":
        return (
          <div className="input-section">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="AI와 대화하세요..."
              disabled={!isConnected}
            />
            <button onClick={sendAIChat} disabled={!isConnected || !message.trim()}>
              AI에게 물어보기
            </button>
          </div>
        );
      case "function":
        return (
          <div className="input-section">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="날씨, 번역, 맞춤법 교정 등을 요청하세요..."
              disabled={!isConnected}
            />
            <button onClick={sendFunctionCall} disabled={!isConnected || !message.trim()}>
              Function Calling
            </button>
          </div>
        );
      case "image":
        return (
          <div className="input-section">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="이미지 설명을 입력하세요..."
              disabled={!isConnected}
            />
            <button onClick={generateImage} disabled={!isConnected || !message.trim()}>
              이미지 생성
            </button>
          </div>
        );
      case "tools":
        return (
          <div className="tools-section">
            <div className="tool-buttons">
              <button onClick={callSpellCheck} disabled={isLoading || !message.trim()}>
                맞춤법 검사
              </button>
              <button onClick={callTranslate} disabled={isLoading || !message.trim()}>
                번역
              </button>
              <button onClick={callWeather} disabled={isLoading || !message.trim()}>
                날씨 확인
              </button>
              <button onClick={callTTS} disabled={isLoading || !message.trim()}>
                음성 변환
              </button>
            </div>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="도구를 사용할 텍스트를 입력하세요..."
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>🤖 AI 통합 채팅 애플리케이션</h1>
        <div className="connection-status">
          {isConnected ? "🟢 연결됨" : "🔴 연결 안됨"}
        </div>
      </header>

      <div className="nickname-bar">
        <input
          type="text"
          placeholder="닉네임을 입력하세요"
          value={inputNickname}
          onChange={(e) => setInputNickname(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleNicknameSet();
          }}
          disabled={!!nickname}
        />
        <button onClick={handleNicknameSet} disabled={!!nickname}>
          입장
        </button>
      </div>

      <div className="main-content">
        <div className="sidebar">
          <div className="tab-buttons">
            <button 
              className={activeTab === "chat" ? "active" : ""} 
              onClick={() => setActiveTab("chat")}
            >
              💬 채팅
            </button>
            <button 
              className={activeTab === "ai" ? "active" : ""} 
              onClick={() => setActiveTab("ai")}
            >
              🤖 AI 챗봇
            </button>
            <button 
              className={activeTab === "function" ? "active" : ""} 
              onClick={() => setActiveTab("function")}
            >
              🔧 Function Calling
            </button>
            <button 
              className={activeTab === "image" ? "active" : ""} 
              onClick={() => setActiveTab("image")}
            >
              🎨 이미지 생성
            </button>
            <button 
              className={activeTab === "tools" ? "active" : ""} 
              onClick={() => setActiveTab("tools")}
            >
              🛠️ 도구
            </button>
          </div>
        </div>

        <div className="chat-area">
          <div className="chat-box">
            {chatLog.map((msg, i) => renderMessage(msg, i))}
            <div ref={messagesEndRef} />
          </div>
          
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
}

export default App;
