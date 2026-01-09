import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Sphere, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

export function DnaHelix() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.getElapsedTime() * 0.5;
    }
  });

  const numPairs = 20;
  const radius = 2;
  const heightStep = 0.5;
  const twist = 0.5;

  return (
    <group ref={groupRef}>
      {Array.from({ length: numPairs }).map((_, i) => {
        const y = (i - numPairs / 2) * heightStep;
        const angle = i * twist;
        
        const x1 = Math.cos(angle) * radius;
        const z1 = Math.sin(angle) * radius;
        
        const x2 = Math.cos(angle + Math.PI) * radius;
        const z2 = Math.sin(angle + Math.PI) * radius;

        return (
          <group key={i} position={[0, y, 0]}>
            {/* Base pair 1 */}
            <mesh position={[x1, 0, z1]}>
              <sphereGeometry args={[0.15, 16, 16]} />
              <meshStandardMaterial color="#2dd4bf" emissive="#14b8a6" emissiveIntensity={0.5} />
            </mesh>
            
            {/* Base pair 2 */}
            <mesh position={[x2, 0, z2]}>
              <sphereGeometry args={[0.15, 16, 16]} />
              <meshStandardMaterial color="#10b981" emissive="#059669" emissiveIntensity={0.5} />
            </mesh>

            {/* Connecting rung */}
            <mesh position={[0, 0, 0]} rotation={[0, 0, angle + Math.PI / 2]}>
              <boxGeometry args={[radius * 2, 0.05, 0.05]} />
              <meshStandardMaterial color="#94a3b8" transparent opacity={0.3} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

export default function DnaModel() {
  return (
    <>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <DnaHelix />
      </Float>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <spotLight position={[-10, 10, 10]} angle={0.15} penumbra={1} intensity={1} />
    </>
  );
}
