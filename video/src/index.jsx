import React from 'react';
import { registerRoot, Composition } from 'remotion';
import { Video } from './Video.jsx';

const Root = () => (
  <Composition id="ShipsOverLand" component={Video} durationInFrames={1398} fps={30} width={1080} height={1920} />
);
registerRoot(Root);
