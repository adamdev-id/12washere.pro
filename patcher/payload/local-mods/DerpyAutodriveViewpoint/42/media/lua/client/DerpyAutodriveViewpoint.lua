-- Native render batches use Viewpoint's current frame, not last frame's UI projection.
-- Keep all changes on StreetRender; do not replace IsoUtils or any camera controls.
local installed = false
local batch = nil
local drawingPlayer = nil
local roadBatch = nil
local collectingRoads = false
local bridgeFault = false
local empty = {}
local maxNumbers = 4096 * 11
local display = {style="Classic line"}
local guidanceSubmitted = false

local function bridge()
    local addons = Viewpoint and Viewpoint.Addons
    local addon = addons and addons["derpy.autodrive-viewpoint"]
    return addon and addon.RouteAddon
end

local function nativeActive()
    if bridgeFault then return false end
    local api = bridge()
    if not api or type(api.active) ~= "function" then return false end
    local ok, enabled = pcall(api.active)
    return ok and enabled == true
end

local function viewpointActive()
    local view = Viewpoint and Viewpoint.View
    if not view or type(view.next) ~= "function" then return false end
    local ok, destination = pcall(view.next)
    -- The API returns the NEXT view: first -> third -> isometric -> first.
    return ok and (destination == "third" or destination == "isometric")
end

local function handles(player)
    return batch ~= nil and player and player:getPlayerNum() == 0
end

local function line(a, b, width, r, g, blue, alpha)
    if not a or not b or not a.x or not a.y or not b.x or not b.y then return end
    -- Half-tile samples keep chords from cutting below crests and changing grades.
    local dx, dy = b.x - a.x, b.y - a.y
    local steps = math.max(1, math.min(2048, math.ceil(math.sqrt(dx * dx + dy * dy) / 0.5)))
    local floor = drawingPlayer and math.floor(drawingPlayer:getZ()) or 0
    local target = collectingRoads and roadBatch or batch
    for step = 1, steps do
        if #target + 11 > maxNumbers then return end
        local t0, t1 = (step - 1) / steps, step / steps
        local n = #target
        target[n + 1], target[n + 2], target[n + 3] = a.x + dx * t0, a.y + dy * t0, floor + 0.05
        target[n + 4], target[n + 5], target[n + 6] = a.x + dx * t1, a.y + dy * t1, floor + 0.05
        target[n + 7], target[n + 8], target[n + 9] = width, r, g
        target[n + 10], target[n + 11] = blue, alpha
    end
end

local function cross(point, r, g, b, alpha)
    if not point or not point.x or not point.y then return end
    line({x=point.x-0.4,y=point.y-0.4}, {x=point.x+0.4,y=point.y+0.4}, 3, r,g,b,alpha)
    line({x=point.x-0.4,y=point.y+0.4}, {x=point.x+0.4,y=point.y-0.4}, 3, r,g,b,alpha)
end

local function polyline(points, width, r,g,b,alpha)
    for i=2, #(points or empty) do line(points[i-1], points[i], width, r,g,b,alpha) end
end

local function pointLength(a, b)
    if not a or not b or type(a.x) ~= "number" or type(a.y) ~= "number"
        or type(b.x) ~= "number" or type(b.y) ~= "number" then return nil end
    local dx, dy = b.x-a.x, b.y-a.y
    return math.sqrt(dx*dx+dy*dy)
end

-- Project onto the route in travel order, using distance along the route to
-- resolve overlapping segments at loops. A distance circle would clip bends wrong.
local function closestAlong(points, point, minimum, preferred)
    local bestDistance, bestPreference, bestAlong = math.huge, math.huge, nil
    local traversed = 0
    for i=2,#points do
        local a, b = points[i-1], points[i]
        local length = pointLength(a,b)
        if not length then return nil end
        if length > 0.0001 and traversed+length >= minimum then
            local dx, dy = b.x-a.x, b.y-a.y
            local t = ((point.x-a.x)*dx+(point.y-a.y)*dy)/(length*length)
            t = math.max(0, math.min(1,t))
            t = math.max(t, (minimum-traversed)/length)
            local x,y = a.x+dx*t, a.y+dy*t
            local distance = (point.x-x)^2+(point.y-y)^2
            local along = traversed+length*t
            local preference = math.abs(along-preferred)
            if distance < bestDistance-0.000001 or
                (math.abs(distance-bestDistance) <= 0.000001 and preference < bestPreference) then
                bestDistance, bestPreference, bestAlong = distance, preference, along
            end
        end
        traversed = traversed+length
    end
    return bestAlong
end

local function yellowHorizon(points, nav, player)
    local api = bridge()
    if not api or type(api.matchGreen) ~= "function" then return nil end
    local ok, matched = pcall(api.matchGreen)
    if not ok or not matched then return nil end
    local data = nav.data and nav.data[player:getPlayerNum()]
    local green = data and data.ctrl and data.ctrl.frenet_pose
    if not green or #green < 2 then return nil end
    local length = 0
    for i=2,#green do
        local segment = pointLength(green[i-1],green[i])
        if not segment then return nil end
        length = length+segment
    end
    if length < 0.0001 then return nil end
    local start = closestAlong(points,green[1],0,0)
    if not start then return nil end
    return closestAlong(points,green[#green],start,start+length)
end

local function readDisplay(api)
    local state={style="Classic line"}
    if api and type(api.ui)=="function" then pcall(api.ui,state) end
    return state
end

local function packPoints(points)
    local out={}
    for i=1,math.min(#points,1024) do
        local p=points[i]
        if not p or type(p.x)~="number" or type(p.y)~="number" then break end
        out[#out+1]=p.x;out[#out+1]=p.y
    end
    return out
end

local function submitGuidance(nav,player,road,path)
    local api=bridge()
    if not display.configured or not api or type(api.guidance)~="function" or not player.getVehicle then return false end
    local car=player:getVehicle()
    local navigating=car and car:isDriver(player) and nav.is_start and nav:is_start(player) or false
    local data=nav.data and nav.data[player:getPlayerNum()]
    local ctrl=data and data.ctrl
    local full={}
    for i=#path,math.max(1,#path-1023),-1 do full[#full+1]=path[i] end
    local a,b=ctrl and ctrl.veh_phead,ctrl and ctrl.veh_ptail
    local fx,fy=0,0
    if a and b then fx,fy=a.x-b.x,a.y-b.y
    elseif #road>=2 then fx,fy=road[2].x-road[1].x,road[2].y-road[1].y end
    local speed=navigating and (ctrl and ctrl.vehicle_speed or car:getCurrentSpeedKmHour()) or 0
    local destination=display.roadVisible and nav.Options.NavLine and road or empty
    local trajectory=display.roadVisible and nav.Options.Traj and ctrl and ctrl.frenet_pose or empty
    local vehicle=car or player
    local ok=pcall(api.guidance,packPoints(destination),packPoints(trajectory),packPoints(full),
        packPoints(ctrl and ctrl.frenet_pose or empty),math.floor(player:getZ()),
        vehicle:getX(),vehicle:getY(),speed,fx,fy,navigating)
    guidanceSubmitted=ok
    return ok
end

local function hudIcon(self,kind,cx,cy,s,alpha,clock,animated,intensity)
    local strength=animated and intensity or 0
    local paths
    if kind=="arrival" then
        paths={{}}
        local radius=23+strength*0.8*math.sin(clock*3)
        alpha=alpha*(1-strength*0.2+strength*0.2*math.sin(clock*3))
        for i=0,24 do local a=i*math.pi/12;paths[1][#paths[1]+1]={math.cos(a)*radius,math.sin(a)*radius} end
        self:drawRect(cx-4*s,cy-4*s,8*s,8*s,alpha,0.75,0.97,1)
    elseif kind=="uturn" then
        paths={{{-15,27},{-15,-10},{-11,-21},{0,-27},{12,-22},{18,-10},{18,16}},{{6,3},{18,16},{30,3}}}
    elseif kind=="right" or kind=="left" then
        local mirror=kind=="left" and -1 or 1
        paths={{{-10*mirror,28},{-10*mirror,6},{-6*mirror,-5},{4*mirror,-13},{29*mirror,-13}},
            {{16*mirror,-26},{29*mirror,-13},{16*mirror,0}}}
    else paths={{{0,29},{0,-28}},{{-17,-10},{0,-28},{17,-10}}} end
    local total=0
    for i=2,#paths[1] do local a,b=paths[1][i-1],paths[1][i];total=total+math.sqrt((b[1]-a[1])^2+(b[2]-a[2])^2) end
    local phase=(clock*0.65)%1.32
    local along=0
    for pathIndex,points in ipairs(paths) do
        for i=2,#points do
            local a,b=points[i-1],points[i]
            self:drawLine(nil,cx+a[1]*s,cy+a[2]*s,cx+b[1]*s,cy+b[2]*s,9*s,alpha*0.10,0.10,0.70,1)
            self:drawLine(nil,cx+a[1]*s,cy+a[2]*s,cx+b[1]*s,cy+b[2]*s,3.2*s,alpha*(1-strength*0.28),0.72,0.96,1)
            if strength>0 and kind~="arrival" then
                local length=math.sqrt((b[1]-a[1])^2+(b[2]-a[2])^2)
                local steps=math.max(1,math.ceil(length/4))
                for step=1,steps do
                    local t0,t1=(step-1)/steps,step/steps
                    local progress=pathIndex==1 and (along+length*(t0+t1)*0.5)/math.max(1,total) or 1.02
                    local trail=(phase-progress+1.32)%1.32
                    local glow=math.max(0,1-trail/0.26)^2*strength
                    if glow>0.015 then
                        local x1,y1=cx+(a[1]+(b[1]-a[1])*t0)*s,cy+(a[2]+(b[2]-a[2])*t0)*s
                        local x2,y2=cx+(a[1]+(b[1]-a[1])*t1)*s,cy+(a[2]+(b[2]-a[2])*t1)*s
                        self:drawLine(nil,x1,y1,x2,y2,8*s,alpha*glow*0.25,0.25,0.9,1)
                        self:drawLine(nil,x1,y1,x2,y2,4*s,alpha*glow,0.95,1,1)
                    end
                end
                if pathIndex==1 then along=along+length end
            end
        end
    end
end

-- A small extruded mesh, projected into the existing HUD and painted by depth.
-- UI polygons use the game's UI renderer; no render-thread camera API calls.
local directionOutline={{0,1.1},{0.58,0.25},{0.23,0.25},{0.23,-1},{-0.23,-1},{-0.23,0.25},{-0.58,0.25}}
local directionFaces={{1,2,7},{3,4,5,6},{14,9,8},{13,12,11,10}}
for i=1,7 do local j=i%7+1;directionFaces[#directionFaces+1]={i,i+7,j+7,j} end

local function hudDirection(self,cx,cy,s,alpha,yaw,pitch,clock,animated,intensity)
    local strength=animated and intensity or 0
    local bob=strength*1.2*math.sin(clock*2.3)
    local pulse=1-strength*0.12+strength*0.12*math.sin(clock*3)
    local cs,sn=math.cos(yaw),math.sin(yaw)
    local cp,sp=math.cos(pitch),math.sin(pitch)
    local vertices={}
    for level=0,1 do
        for _,point in ipairs(directionOutline) do
            local x,z=point[1]*cs+point[2]*sn,point[2]*cs-point[1]*sn
            local y=(level==0 and 0.13 or -0.13)
            y,z=y*cp+z*sp,z*cp-y*sp
            local up,depth=y*0.63+z*0.78,z*0.63-y*0.78
            local perspective=4/(4+depth)
            vertices[#vertices+1]={cx+x*26*s*perspective,cy-up*26*s*perspective+bob*s,depth,x,up,depth}
        end
    end
    local faces={}
    for _,indices in ipairs(directionFaces) do
        local depth=0;for _,i in ipairs(indices) do depth=depth+vertices[i][3] end
        faces[#faces+1]={indices=indices,depth=depth/#indices}
    end
    table.sort(faces,function(a,b) return a.depth>b.depth end)
    for _,face in ipairs(faces) do
        local indices=face.indices
        local a,b,c=vertices[indices[1]],vertices[indices[2]],vertices[indices[3]]
        local d=vertices[indices[4] or indices[3]]
        local ux,uy,uz=b[4]-a[4],b[5]-a[5],b[6]-a[6]
        local vx,vy,vz=c[4]-a[4],c[5]-a[5],c[6]-a[6]
        local nx,ny,nz=uy*vz-uz*vy,uz*vx-ux*vz,ux*vy-uy*vx
        local norm=math.sqrt(nx*nx+ny*ny+nz*nz)
        local light=0.28+0.72*math.max(0,(-nx*0.35+ny*0.75-nz*0.55)/math.max(0.001,norm))
        self:drawPolygon(nil,a[1],a[2],b[1],b[2],c[1],c[2],d[1],d[2],
            0.12+light*0.68,0.38+light*0.58,0.62+light*0.38,alpha*pulse)
        for i=1,#indices do
            local p,q=vertices[indices[i]],vertices[indices[i%#indices+1]]
            self:drawLine(nil,p[1],p[2],q[1],q[2],s,alpha*0.4*pulse,0.45,0.92,1)
        end
    end
end

local function renderHUD(self,state)
    if not state.hudVisible then
        self.derpyHUDAlpha=0;self.derpyHUDTime=nil;self.derpyHUDYaw=nil;self.derpyHUDPitch=nil
        self.derpyHUDAnimation=0;self.derpyHUDArrowStyle=nil;return
    end
    local now=getTimeInMillis()
    local target=(state.fade or 1)*(state.brightness or 0.9)
    local dt=self.derpyHUDTime and math.max(0,math.min(0.1,(now-self.derpyHUDTime)/1000)) or 0.1
    self.derpyHUDTime=now
    self.derpyHUDAlpha=(self.derpyHUDAlpha or 0)+(target-(self.derpyHUDAlpha or 0))*(1-math.exp(-dt*8))
    local alpha=self.derpyHUDAlpha
    if alpha<0.01 then return end
    local s=state.hudScale or 1
    local sw,sh=getCore():getScreenWidth(),getCore():getScreenHeight()
    -- Keep the complete HUD in view even at small resolutions and maximum scale.
    s=math.min(s,(sw-32)/282,(sh-32)/120)
    local w,h=282*s,120*s
    local x,y=(sw-w)/2,sh*0.76-h/2
    if state.hudPosition=="Lower left" then x=40
    elseif state.hudPosition=="Lower right" then x=sw-w-40
    elseif state.hudPosition=="Upper centre" then y=sh*0.20-h/2 end
    x=math.max(16,math.min(sw-w-16,x));y=math.max(16,math.min(sh-h-16,y))
    self:drawRect(x,y,w,h,alpha*0.16,0.015,0.04,0.07)
    for _,corner in ipairs({{x,y,1,1},{x+w,y,-1,1},{x,y+h,1,-1},{x+w,y+h,-1,-1}}) do
        self:drawLine(nil,corner[1],corner[2],corner[1]+corner[3]*17*s,corner[2],1,alpha*0.35,0.25,0.85,1)
        self:drawLine(nil,corner[1],corner[2],corner[1],corner[2]+corner[4]*12*s,1,alpha*0.35,0.25,0.85,1)
    end
    local kind=state.turn or "straight"
    local animated=state.hudArrowAnimated~=false
    local intensity=math.max(0,math.min(1,state.hudArrowAnimationIntensity or 0.7))
    if animated then self.derpyHUDAnimation=(self.derpyHUDAnimation or 0)+dt*(state.hudArrowAnimationSpeed or 1) end
    local clock=self.derpyHUDAnimation or 0
    local style=state.hudArrowStyle or "3D Direction Arrow"
    if style=="3D Direction Arrow" and kind~="arrival" then
        local yaw,pitch=state.directionYaw or 0,state.directionPitch or 0
        if not self.derpyHUDYaw or self.derpyHUDArrowStyle~=style then self.derpyHUDYaw=yaw;self.derpyHUDPitch=pitch end
        local smoothness=math.max(0.05,math.min(1,state.directionSmoothness or 0.3))
        local blend=1-math.exp(-dt/smoothness)
        local delta=math.atan2(math.sin(yaw-self.derpyHUDYaw),math.cos(yaw-self.derpyHUDYaw))
        self.derpyHUDYaw=self.derpyHUDYaw+delta*blend
        self.derpyHUDPitch=self.derpyHUDPitch+(pitch-self.derpyHUDPitch)*blend
        hudDirection(self,x+53*s,y+60*s,s,alpha,self.derpyHUDYaw,self.derpyHUDPitch,clock,animated,intensity)
    else hudIcon(self,kind,x+53*s,y+60*s,s,alpha,clock,animated,intensity) end
    self.derpyHUDArrowStyle=style
    local distance=math.max(0,state.distance or 0)
    local text=distance>=1000 and string.format("%.1f km",distance/1000) or string.format("%.0f m",distance)
    if kind=="arrival" then text="ARRIVED" end
    local labels={left="TURN LEFT",right="TURN RIGHT",uturn="MAKE A U-TURN",arrival="DESTINATION",straight="FOLLOW ROUTE"}
    self:drawTextZoomed("AUTODRIVE",x+105*s,y+13*s,0.72*s,0.45,0.80,0.92,alpha*0.75,UIFont.Small)
    self:drawTextZoomed(text,x+103*s,y+34*s,1.25*s,0.90,0.99,1,alpha,UIFont.Large)
    self:drawTextZoomed(labels[kind] or labels.straight,x+105*s,y+74*s,0.8*s,0.65,0.89,0.98,alpha,UIFont.Small)
    self:drawRect(x+105*s,y+101*s,147*s,2*s,alpha*0.18,0.30,0.80,1)
    self:drawRect(x+105*s,y+101*s,147*s*math.max(0,math.min(1,1-distance/120)),2*s,alpha*0.85,0.30,0.88,1)
end

local function install()
    if installed or not StreetRender or not MapForNav then return end
    installed = true
    local originalRender = StreetRender.render
    local originalRoad = StreetRender.render_RoadLine
    local originalRoute = StreetRender.render_NavLine
    local originalManual = StreetRender.render_ManualRoadLine
    local originalTrajectory = StreetRender.render_Traj
    local originalDebug = StreetRender.render_Debug

    function StreetRender:render_RoadLine(nav, player, light)
        if not handles(player) then return originalRoad(self, nav, player, light) end
        drawingPlayer = player
        if display.roadVisible==false then return end
        local opts = nav.Options
        if not opts.RoadLine and not opts.ManualStreets then return end
        if nav.step ~= "idle" then return end
        local data = nav.data and nav.data[0]
        if not data then return end
        local groups = {data.render_asphalt or empty, data.render_dirt or empty, data.render_railway or empty}
        local colours = {{0.45,0.75,0.90},{0.90,0.78,0.45},{0.75,0.65,0.95}}
        collectingRoads = true
        for i=1,3 do
            local c = colours[i]
            for _, point in ipairs(groups[i]) do
                local nextPoint = point.next and nav.nodes and nav.nodes[point.next]
                line(point, nextPoint, 2, c[1],c[2],c[3], 0.25 + light * 0.25)
                for fork,_ in pairs(point.fork or empty) do
                    line(point, fork, 2, 0.50,0.85,0.60, 0.25 + light * 0.25)
                end
            end
        end
        collectingRoads = false
    end

    function StreetRender:render_NavLine(nav, player, light)
        if not handles(player) then return originalRoute(self, nav, player, light) end
        drawingPlayer = player
        if not nav.Options.NavLine and not display.configured then return end
        local path = nav:get_nav_path(player) or empty
        -- Same six nearby route nodes as Autodrive's vanilla overlay.
        local points = {}
        for i=#path,math.max(1,#path-5),-1 do points[#points+1] = path[i] end
        local remaining = yellowHorizon(points,nav,player)
        local road={}
        if points[1] then road[1]=points[1] end
        for i=2,#points do
            local a,b = points[i-1],points[i]
            local length = pointLength(a,b)
            if not length then break end
            if remaining ~= nil then
                if remaining <= 0.0001 then break end
                if length > remaining then
                    local t = remaining/length
                    b = {x=a.x+(b.x-a.x)*t, y=a.y+(b.y-a.y)*t}
                end
            end
            road[#road+1]=b
            if remaining ~= nil then remaining = remaining-length end
        end
        if not submitGuidance(nav,player,road,path) and nav.Options.NavLine and display.roadVisible~=false then
            for _,goal in ipairs(nav:get_goals(player) or empty) do cross(goal,1,1,0,0.8) end
            polyline(road,3,1,1,0,0.55+light*0.25)
        end
    end

    function StreetRender:render_ManualRoadLine(nav, player, light)
        if not handles(player) then return originalManual(self, nav, player, light) end
        drawingPlayer = player
        if display.roadVisible==false or not nav.Options.ManualStreets or nav.step ~= "idle" then return end
        local data = nav.data and nav.data[0]
        if not data then return end
        for _, points in pairs(data.render_manual_steets or empty) do
            polyline(points, 3, 0.90,0.55,0.70,0.8)
            polyline(points.left, 2, 0.10,0.55,0.70,0.6)
            polyline(points.right, 2, 0.10,0.55,0.70,0.6)
        end
        cross(data.manual_point, 1,1,1,1)
        cross(data.manual_street_point and data.manual_street_point.pose, 1,0,0.5,1)
    end

    function StreetRender:render_Traj(nav, player, light)
        if not handles(player) then return originalTrajectory(self, nav, player, light) end
        drawingPlayer = player
        if display.configured or display.roadVisible==false or not nav.Options.Traj then return end
        local data = nav.data and nav.data[0]
        local ctrl = data and data.ctrl
        if not ctrl or not ctrl.frenet_pose then return end
        polyline(ctrl.frenet_pose, 2, 0.15,1,0.25, 0.5 + light * 0.25)
    end

    function StreetRender:render_Debug(nav, player, light)
        -- Vanilla diagnostic labels use the flat isometric projection.
        if handles(player) then return end
        return originalDebug(self, nav, player, light)
    end

    function StreetRender:render()
        local api = bridge()
        if not nativeActive() then
            batch, roadBatch, drawingPlayer = nil, nil, nil
            if api and api.submit then pcall(api.submit, empty) end
            if api and api.clearGuidance then pcall(api.clearGuidance) end
            -- Never draw vanilla's flat projection in a 3D view while waiting
            -- for a camera snapshot, add-on enable, or a recoverable transition.
            if viewpointActive() then return end
            return originalRender(self)
        end
        display=readDisplay(api)
        guidanceSubmitted=false
        batch, roadBatch, collectingRoads = {}, {}, false
        local ok, problem = pcall(originalRender, self)
        local ready = batch
        -- Routes take priority when a dense road network reaches the batch limit.
        for i=1, math.min(#roadBatch, maxNumbers - #ready) do ready[#ready+1] = roadBatch[i] end
        batch, roadBatch, drawingPlayer, collectingRoads = nil, nil, nil, false
        if ok then
            local sent, reason = pcall(api.submit, ready)
            if not sent then
                bridgeFault = true
                print("[DerpyViewpoint] Route batch failed; using original overlay: " .. tostring(reason))
            end
            if not guidanceSubmitted and api.clearGuidance then pcall(api.clearGuidance) end
            renderHUD(self,readDisplay(api))
        else
            pcall(api.submit, empty)
            if api.clearGuidance then pcall(api.clearGuidance) end
            error(problem)
        end
    end
    print("[DerpyViewpoint] Overlay adapter installed; waiting for Viewpoint render add-on.")
end

Events.OnGameStart.Add(install)
Events.OnMainMenuEnter.Add(install)
Events.OnTick.Add(function() if not installed then install() end end)
