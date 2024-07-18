import System.Environment (getArgs)

-- 定义设备和状态
data Device = Bulb | Switch | Outlet deriving (Show, Eq)
data BulbState = Off | On deriving (Show, Eq)
data SwitchState = SwitchOff | SwitchOn deriving (Show, Eq)
data OutletState = Powered | Unpowered deriving (Show, Eq)


-- 设备状态
data DeviceState = BulbState BulbState
                 | SwitchState SwitchState
                 | OutletState OutletState
                 deriving (Show, Eq)

-- 系统状态
type SystemState = [(Device, DeviceState)]

type ChainReaction = SystemState -> Device -> DeviceState -> SystemState

-- 更新系统状态，确保插座、开关和灯泡的状态正确反映
updateState :: SystemState -> Device -> DeviceState -> SystemState
updateState state device newState =
  map (\(dev, st) -> if dev == device then (dev, newState) else (dev, st)) state

-- 根据开关更新灯泡状态
updateBulbBasedOnSwitch :: SystemState -> DeviceState -> SystemState
updateBulbBasedOnSwitch state (SwitchState SwitchOn) =
    let outletState = lookup Outlet state
    in case outletState of
        Just (OutletState Powered) -> updateState (updateState state Switch (SwitchState SwitchOn)) Bulb (BulbState On) -- 灯泡状态调整为Dim仅当插座通电，并更新开关状态为On
        _ -> updateState state Switch (SwitchState SwitchOn) -- 更新开关状态为On，但不改变灯泡状态
updateBulbBasedOnSwitch state (SwitchState SwitchOff) = updateState (updateState state Bulb (BulbState Off)) Switch (SwitchState SwitchOff) -- 关闭灯泡并更新开关状态为Off
updateBulbBasedOnSwitch state _ = state

updateBulbWithOutletAndSwitch :: SystemState -> SystemState
updateBulbWithOutletAndSwitch state =
  let outletState = lookup Outlet state
      switchState = lookup Switch state
  in case (outletState, switchState) of
      (Just (OutletState Powered), Just (SwitchState SwitchOn)) -> updateState state Bulb (BulbState On)
      _ -> updateState state Bulb (BulbState Off)

updateBulbBasedOnOutletAndSwitch :: SystemState -> DeviceState -> SystemState
updateBulbBasedOnOutletAndSwitch state newState =
  case newState of
    OutletState Powered -> updateBulbWithOutletAndSwitch state
    OutletState Unpowered -> updateState (updateState state Outlet (OutletState Unpowered)) Bulb (BulbState Off)
    SwitchState SwitchOn -> updateBulbWithOutletAndSwitch (updateState state Switch (SwitchState SwitchOn))
    SwitchState SwitchOff -> updateState state Switch (SwitchState SwitchOff)
    _ -> state


-- 根据插座更新灯泡状态
updateBulbBasedOnOutlet :: SystemState -> DeviceState -> SystemState
updateBulbBasedOnOutlet state (OutletState Powered) =
    let switchState = lookup Switch state
    in case switchState of
        Just (SwitchState SwitchOn) -> updateState (updateState state Outlet (OutletState Powered)) Bulb (BulbState On) -- 插座通电且开关为开时，灯泡调整为Dim
        _ -> updateState state Outlet (OutletState Powered) -- 仅更新插座状态为Powered
updateBulbBasedOnOutlet state (OutletState Unpowered) = updateState (updateState state Outlet (OutletState Unpowered)) Bulb (BulbState Off) -- 断电插座并关闭灯泡
updateBulbBasedOnOutlet state _ = state

-- 处理状态变化和连锁反应
-- handleStateChange :: ChainReaction
-- handleStateChange state device newState =
--   case device of
--     Switch -> updateBulbBasedOnSwitch state newState
--     Outlet -> updateBulbBasedOnOutlet state newState
--     Bulb -> updateState state device newState

handleStateChange :: ChainReaction
handleStateChange state device newState =
  case (device, newState) of
    (Switch, SwitchState switchState) -> updateBulbBasedOnOutletAndSwitch state (SwitchState switchState)
    (Outlet, OutletState outletState) -> updateBulbBasedOnOutletAndSwitch state (OutletState outletState)
    (Bulb, BulbState bulbState) -> updateState state Bulb (BulbState bulbState)
    _ -> state  -- 保持原状态如果类型不匹配



instance Read Device where
    readsPrec _ value = case value of
        "Bulb"   -> [(Bulb, "")]
        "Switch" -> [(Switch, "")]
        "Outlet" -> [(Outlet, "")]
        _        -> []

instance Read DeviceState where
    readsPrec _ value =
        let bulbStates = [("Off", BulbState Off), ("On", BulbState On)]
            switchStates = [("SwitchOff", SwitchState SwitchOff), ("SwitchOn", SwitchState SwitchOn)]
            outletStates = [("Powered", OutletState Powered), ("Unpowered", OutletState Unpowered)]
            tryRead s lst = [(state, rest) | (str, state) <- lst, (s, rest) <- lex value, s == str]
        in tryRead value bulbStates ++ tryRead value switchStates ++ tryRead value outletStates

-- ./temp Bulb Dim
main :: IO ()
main = do
  let initialState = [(Bulb, BulbState Off), (Switch, SwitchState SwitchOff), (Outlet, OutletState Unpowered)]
  
  putStrLn "Initial State:"
  print initialState

  args <- getArgs
  if length args < 2 then
    putStrLn "Error: Not enough arguments. Usage: <executable> <Device> <DeviceState>"
  else do
    let (deviceStr, stateStr) = (args !! 0, args !! 1)
        device = read deviceStr :: Device
        newState = read stateStr :: DeviceState
        newStateAfterChange = handleStateChange initialState device newState

    putStrLn "State after change:"
    print newStateAfterChange

