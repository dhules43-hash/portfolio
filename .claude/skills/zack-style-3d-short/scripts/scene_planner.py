"""Scene plan shared by BOTH pipelines (software renderer + Blender)."""
SCENES = [
 dict(id=1, t0=0, t1=4.6,  name="Forbidden",   env="office",   shots="over-the-shoulder push-in -> low-angle", sfx=["rumble","slam@2.2"],
      text="Nineteen twenty-nine. A young doctor is told: never try this."),
 dict(id=2, t0=4.6, t1=10.2,  name="Self-test",   env="operating room", shots="extreme close-up eyes -> macro syringe -> orbit arm", sfx=["whoosh@4.0","needle@6.2","slide@7.4"],
      text="Werner Forssmann ignored his boss, numbed his arm, and slid a thin tube into a vein."),
 dict(id=3, t0=10.2, t1=14.8, name="Journey",     env="vein + heart", shots="first-person fly-through -> heart orbit", sfx=["whoosh@9.0","heartbeat"],
      text="Then he pushed it upward, inch by inch, until it reached his heart."),
 dict(id=4, t0=14.8, t1=18.7, name="Walk",        env="corridor", shots="side tracking -> front dolly-back", sfx=["whoosh@14.0","steps"],
      text="With the tube still inside him, he walked to the X-ray room."),
 dict(id=5, t0=18.7, t1=23.1, name="X-ray",       env="x-ray room", shots="push-in -> extreme close-up", sfx=["hum","flash@21.0"],
      text="The X-ray proved it: a catheter could safely enter a living heart."),
 dict(id=6, t0=23.1, t1=26.4, name="Punished",    env="office (red)", shots="close-up -> close-up -> wide", sfx=["slam@23.0","door@25.6"],
      text="His boss was furious. He was punished for it."),
 dict(id=7, t0=26.4, t1=30, name="Nobel",       env="stage", shots="medal orbit -> pull back reveal", sfx=["chime@26.0","sparkle","applause"],
      text="But in nineteen fifty-six, he shared the Nobel Prize."),
]
KEYWORDS = {"forbidden","never","heart","tube","vein","x-ray","nobel","prize","punished","furious","proved","inch"}
