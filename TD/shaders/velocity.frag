layout(location=0) out vec4 fragColor;
uniform vec4 uPointer;
uniform vec4 uStep;
uniform float uReset;
uniform float uDamping;
void main() {
    vec2 uv=vUV.st, size=uTD2DInfos[0].res.zw;
    vec2 velocity=texture(sTD2DInputs[0],uv).xy;
    velocity=texture(sTD2DInputs[0],clamp(uv-uStep.x*velocity/size,vec2(0),vec2(1))).xy;
    velocity*=exp(-uDamping*uStep.x);
    vec2 distance=(uv-uPointer.xy)*vec2(1280.0/647.0,1.0);
    float brush=exp(-dot(distance,distance)/max(uStep.z*uStep.z,0.000001));
    velocity+=uPointer.zw*size*uStep.y*brush;
    velocity=clamp(velocity,vec2(-700),vec2(700));
    if(uReset>0.5) velocity=vec2(0);
    fragColor=TDOutputSwizzle(vec4(velocity,0,1));
}
