export function rafLoop(render) {
  let active = true;
  function frame(ts) {
    if (!active) {
      return;
    }
    render(ts);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  return () => {
    active = false;
  };
}
