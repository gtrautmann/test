import { useState, useEffect, useRef, useCallback } from "react";
import lyrics from "./lyrics";

const LINE_DURATION = 2800;
const BLANK_LINE_DURATION = 800;
const SECTION_PAUSE = 1500;

function getSectionColor(section) {
  if (section.includes("Chorus")) return "#f0c040";
  if (section.includes("Bridge")) return "#e07040";
  if (section.includes("Intro") || section.includes("Outro")) return "#90b8f0";
  if (section.includes("Pre-Chorus")) return "#b8a0e0";
  return "#d0d8e8";
}

function getSectionGlow(section) {
  if (section.includes("Chorus")) return "0 0 40px rgba(240, 192, 64, 0.4)";
  if (section.includes("Bridge")) return "0 0 40px rgba(224, 112, 64, 0.3)";
  if (section.includes("Pre-Chorus")) return "0 0 30px rgba(184, 160, 224, 0.3)";
  return "none";
}

export default function LyricsVisualizer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentSection, setCurrentSection] = useState(-1);
  const [currentLine, setCurrentLine] = useState(-1);
  const [revealedLines, setRevealedLines] = useState([]);
  const [showTitle, setShowTitle] = useState(true);
  const [finished, setFinished] = useState(false);
  const containerRef = useRef(null);
  const timeoutRef = useRef(null);
  const isPlayingRef = useRef(false);

  const scrollToBottom = useCallback(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, []);

  const stop = useCallback(() => {
    isPlayingRef.current = false;
    setIsPlaying(false);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  }, []);

  const reset = useCallback(() => {
    stop();
    setCurrentSection(-1);
    setCurrentLine(-1);
    setRevealedLines([]);
    setShowTitle(true);
    setFinished(false);
  }, [stop]);

  const play = useCallback(() => {
    reset();
    setShowTitle(false);
    setIsPlaying(true);
    isPlayingRef.current = true;

    let sIdx = 0;
    let lIdx = 0;

    const revealNext = () => {
      if (!isPlayingRef.current) return;

      if (sIdx >= lyrics.length) {
        setFinished(true);
        isPlayingRef.current = false;
        setIsPlaying(false);
        return;
      }

      const section = lyrics[sIdx];
      setCurrentSection(sIdx);
      setCurrentLine(lIdx);

      const line = section.lines[lIdx];
      const isBlank = line === "";

      setRevealedLines((prev) => [...prev, { sIdx, lIdx, text: line }]);

      setTimeout(scrollToBottom, 100);

      lIdx++;
      if (lIdx >= section.lines.length) {
        sIdx++;
        lIdx = 0;
        const delay = isBlank ? BLANK_LINE_DURATION : LINE_DURATION;
        timeoutRef.current = setTimeout(revealNext, delay + SECTION_PAUSE);
      } else {
        const delay = isBlank ? BLANK_LINE_DURATION : LINE_DURATION;
        timeoutRef.current = setTimeout(revealNext, delay);
      }
    };

    timeoutRef.current = setTimeout(revealNext, 1000);
  }, [reset, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  const allLines = [];
  let globalIdx = 0;
  lyrics.forEach((section, sIdx) => {
    allLines.push({ type: "section", text: section.section, sIdx, key: `s-${sIdx}` });
    section.lines.forEach((line, lIdx) => {
      allLines.push({
        type: "line",
        text: line,
        sIdx,
        lIdx,
        globalIdx: globalIdx++,
        key: `l-${sIdx}-${lIdx}`,
      });
    });
  });

  const isRevealed = (sIdx, lIdx) =>
    revealedLines.some((r) => r.sIdx === sIdx && r.lIdx === lIdx);

  const isCurrentLine = (sIdx, lIdx) =>
    currentSection === sIdx && currentLine === lIdx;

  return (
    <div style={styles.wrapper}>
      {showTitle && (
        <div style={styles.titleScreen}>
          <h1 style={styles.title}>I Will Stand in the Light</h1>
          <p style={styles.subtitle}>A Lyrics Visualizer</p>
          <button onClick={play} style={styles.playButton}>
            Play
          </button>
        </div>
      )}

      {!showTitle && (
        <>
          <div style={styles.header}>
            <h2 style={styles.headerTitle}>I Will Stand in the Light</h2>
            {currentSection >= 0 && (
              <span
                style={{
                  ...styles.sectionBadge,
                  background: getSectionColor(lyrics[currentSection]?.section || ""),
                }}
              >
                {lyrics[currentSection]?.section}
              </span>
            )}
          </div>

          <div ref={containerRef} style={styles.lyricsContainer}>
            <div style={styles.lyricsInner}>
              {allLines.map((item) => {
                if (item.type === "section") {
                  const sectionRevealed = revealedLines.some(
                    (r) => r.sIdx === item.sIdx
                  );
                  return (
                    <div
                      key={item.key}
                      style={{
                        ...styles.sectionLabel,
                        color: getSectionColor(item.text),
                        opacity: sectionRevealed ? 1 : 0,
                        transform: sectionRevealed
                          ? "translateY(0)"
                          : "translateY(10px)",
                      }}
                    >
                      {item.text}
                    </div>
                  );
                }

                const revealed = isRevealed(item.sIdx, item.lIdx);
                const isCurrent = isCurrentLine(item.sIdx, item.lIdx);
                const section = lyrics[item.sIdx].section;
                const color = getSectionColor(section);

                if (item.text === "") {
                  return (
                    <div key={item.key} style={{ height: "1.2em" }} />
                  );
                }

                return (
                  <div
                    key={item.key}
                    style={{
                      ...styles.lyricLine,
                      opacity: revealed ? 1 : 0,
                      transform: revealed
                        ? "translateY(0) scale(1)"
                        : "translateY(20px) scale(0.95)",
                      color: isCurrent ? color : revealed ? "#c8ccd4" : "#444",
                      textShadow: isCurrent ? getSectionGlow(section) : "none",
                      fontSize: section.includes("Chorus") || section.includes("Bridge")
                        ? "1.6rem"
                        : "1.35rem",
                      fontWeight: isCurrent ? 700 : section.includes("Chorus") ? 600 : 400,
                    }}
                  >
                    {item.text}
                  </div>
                );
              })}

              {finished && (
                <div style={styles.finishedContainer}>
                  <div style={styles.finishedLine} />
                  <p style={styles.finishedText}>- End -</p>
                </div>
              )}
            </div>
          </div>

          <div style={styles.controls}>
            {isPlaying ? (
              <button onClick={stop} style={styles.controlButton}>
                Stop
              </button>
            ) : (
              <button onClick={play} style={styles.controlButton}>
                {finished ? "Replay" : "Play"}
              </button>
            )}
            <button onClick={reset} style={styles.controlButtonSecondary}>
              Reset
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const styles = {
  wrapper: {
    position: "relative",
    zIndex: 1,
    width: "100%",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    color: "#e0e0e0",
    fontFamily: "'Georgia', 'Times New Roman', serif",
  },
  titleScreen: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100%",
    textAlign: "center",
    animation: "fadeIn 2s ease",
  },
  title: {
    fontSize: "3.5rem",
    fontWeight: 300,
    color: "#f0c040",
    textShadow: "0 0 60px rgba(240, 192, 64, 0.4), 0 0 120px rgba(240, 192, 64, 0.15)",
    marginBottom: "0.5rem",
    letterSpacing: "0.04em",
  },
  subtitle: {
    fontSize: "1.2rem",
    color: "#888",
    marginBottom: "3rem",
    fontStyle: "italic",
  },
  playButton: {
    padding: "16px 60px",
    fontSize: "1.2rem",
    background: "linear-gradient(135deg, #f0c040, #e0a020)",
    color: "#1a1a2e",
    border: "none",
    borderRadius: "50px",
    cursor: "pointer",
    fontWeight: 600,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
    transition: "all 0.3s",
    boxShadow: "0 0 30px rgba(240, 192, 64, 0.3)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "1rem",
    padding: "1.5rem 2rem",
    width: "100%",
    maxWidth: "800px",
  },
  headerTitle: {
    fontSize: "1.1rem",
    fontWeight: 400,
    color: "#777",
    margin: 0,
  },
  sectionBadge: {
    padding: "4px 14px",
    borderRadius: "20px",
    fontSize: "0.75rem",
    fontWeight: 600,
    color: "#1a1a2e",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    transition: "all 0.5s ease",
  },
  lyricsContainer: {
    flex: 1,
    overflow: "auto",
    width: "100%",
    maxWidth: "800px",
    padding: "0 2rem",
    scrollbarWidth: "thin",
    scrollbarColor: "#333 transparent",
  },
  lyricsInner: {
    paddingBottom: "40vh",
  },
  sectionLabel: {
    fontSize: "0.8rem",
    fontWeight: 600,
    textTransform: "uppercase",
    letterSpacing: "0.15em",
    marginTop: "2.5rem",
    marginBottom: "1rem",
    transition: "all 0.8s ease",
  },
  lyricLine: {
    lineHeight: 1.9,
    transition: "all 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    padding: "2px 0",
  },
  finishedContainer: {
    marginTop: "3rem",
    textAlign: "center",
    animation: "fadeIn 2s ease",
  },
  finishedLine: {
    width: "60px",
    height: "1px",
    background: "linear-gradient(to right, transparent, #f0c040, transparent)",
    margin: "0 auto 1rem",
  },
  finishedText: {
    color: "#666",
    fontStyle: "italic",
    fontSize: "1rem",
  },
  controls: {
    display: "flex",
    gap: "1rem",
    padding: "1.5rem",
  },
  controlButton: {
    padding: "10px 36px",
    fontSize: "0.95rem",
    background: "linear-gradient(135deg, #f0c040, #e0a020)",
    color: "#1a1a2e",
    border: "none",
    borderRadius: "30px",
    cursor: "pointer",
    fontWeight: 600,
    letterSpacing: "0.05em",
    transition: "all 0.3s",
  },
  controlButtonSecondary: {
    padding: "10px 36px",
    fontSize: "0.95rem",
    background: "transparent",
    color: "#888",
    border: "1px solid #444",
    borderRadius: "30px",
    cursor: "pointer",
    fontWeight: 400,
    letterSpacing: "0.05em",
    transition: "all 0.3s",
  },
};
