#import "HCSafeOverlay.h"

@interface HCPassthroughWindow : UIWindow
@end

@implementation HCPassthroughWindow
- (UIView *)hitTest:(CGPoint)point withEvent:(UIEvent *)event {
    UIView *hit = [super hitTest:point withEvent:event];
    return hit == self.rootViewController.view ? nil : hit;
}
@end

@interface HCSafeOverlay ()
@property(nonatomic, copy) NSString *expectedBundleID;
@property(nonatomic, copy) NSString *expectedVersion;
@property(nonatomic, assign) BOOL mappingPassed;
@property(nonatomic, strong) UIWindow *overlayWindow;
@property(nonatomic, strong) UIButton *floatButton;
@property(nonatomic, strong) UIView *panelView;
@property(nonatomic, strong) UILabel *statusLabel;
@property(nonatomic, assign, readwrite) BOOL panelVisible;
@property(nonatomic, copy, readwrite) NSString *status;
@end

@implementation HCSafeOverlay

- (instancetype)initWithExpectedBundleID:(NSString *)bundleID
                                version:(NSString *)version
                         mappingPassed:(BOOL)mappingPassed {
    self = [super init];
    if (!self) return nil;
    _expectedBundleID = [bundleID copy];
    _expectedVersion = [version copy];
    _mappingPassed = mappingPassed;
    _status = @"closed";
    return self;
}

- (void)installOnMainWindow:(UIWindow *)mainWindow {
    NSAssert([NSThread isMainThread], @"HCSafeOverlay must be installed on main thread");
    if (self.overlayWindow || !mainWindow) return;

    UIWindowScene *scene = mainWindow.windowScene;
    if (!scene) return;

    UIWindow *window = [[HCPassthroughWindow alloc] initWithWindowScene:scene];
    window.frame = mainWindow.bounds;
    window.windowLevel = UIWindowLevelAlert + 1;
    window.backgroundColor = UIColor.clearColor;
    window.rootViewController = [UIViewController new];

    UIButton *button = [UIButton buttonWithType:UIButtonTypeSystem];
    button.frame = CGRectMake(18.0, 120.0, 64.0, 64.0);
    button.layer.cornerRadius = 32.0;
    button.backgroundColor = [UIColor colorWithRed:0.12 green:0.44 blue:0.86 alpha:0.94];
    [button setTitle:@"HC" forState:UIControlStateNormal];
    [button setTitleColor:UIColor.whiteColor forState:UIControlStateNormal];
    [button addTarget:self action:@selector(handleFloatButton:) forControlEvents:UIControlEventTouchUpInside];
    [window.rootViewController.view addSubview:button];

    self.overlayWindow = window;
    self.floatButton = button;
    window.hidden = NO;
}

- (void)handleFloatButton:(UIButton *)sender {
    (void)sender;
    NSAssert([NSThread isMainThread], @"UI action must stay on main thread");

    // Gate before panel work. There is deliberately no game/native bridge here.
    NSString *bundleID = NSBundle.mainBundle.bundleIdentifier ?: @"";
    NSString *version = NSBundle.mainBundle.infoDictionary[@"CFBundleShortVersionString"] ?: @"";
    BOOL compatible = [bundleID isEqualToString:self.expectedBundleID] &&
                      [version isEqualToString:self.expectedVersion] &&
                      self.mappingPassed;
    if (!compatible) {
        self.status = @"blocked";
        self.panelVisible = NO;
        [self.panelView removeFromSuperview];
        self.panelView = nil;
        self.statusLabel = nil;
        return;
    }

    if (self.panelVisible) {
        self.panelVisible = NO;
        self.status = @"closed";
        [self.panelView removeFromSuperview];
        self.panelView = nil;
        self.statusLabel = nil;
        return;
    }

    self.panelVisible = YES;
    self.status = @"ui_only";
    [self showUIOnlyPanel];
}

- (void)showUIOnlyPanel {
    UIView *panel = [[UIView alloc] initWithFrame:CGRectMake(96.0, 112.0, 260.0, 180.0)];
    panel.backgroundColor = [UIColor colorWithWhite:0.08 alpha:0.96];
    panel.layer.cornerRadius = 12.0;

    UILabel *title = [[UILabel alloc] initWithFrame:CGRectMake(16.0, 16.0, 228.0, 28.0)];
    title.text = @"Her Comeback Tools";
    title.textColor = UIColor.whiteColor;
    title.font = [UIFont boldSystemFontOfSize:17.0];
    [panel addSubview:title];

    UILabel *status = [[UILabel alloc] initWithFrame:CGRectMake(16.0, 58.0, 228.0, 70.0)];
    status.numberOfLines = 0;
    status.text = @"UI-only diagnostic mode\nNo game data bridge attached";
    status.textColor = [UIColor colorWithWhite:0.82 alpha:1.0];
    status.font = [UIFont systemFontOfSize:14.0];
    [panel addSubview:status];

    UIButton *close = [UIButton buttonWithType:UIButtonTypeSystem];
    close.frame = CGRectMake(16.0, 136.0, 228.0, 30.0);
    [close setTitle:@"Close" forState:UIControlStateNormal];
    [close setTitleColor:[UIColor colorWithRed:0.35 green:0.68 blue:1.0 alpha:1.0] forState:UIControlStateNormal];
    [close addTarget:self action:@selector(closePanel:) forControlEvents:UIControlEventTouchUpInside];
    [panel addSubview:close];

    [self.overlayWindow.rootViewController.view addSubview:panel];
    self.panelView = panel;
    self.statusLabel = status;
}

- (void)closePanel:(UIButton *)sender {
    (void)sender;
    self.panelVisible = NO;
    self.status = @"closed";
    [self.panelView removeFromSuperview];
    self.panelView = nil;
    self.statusLabel = nil;
}

- (void)remove {
    NSAssert([NSThread isMainThread], @"HCSafeOverlay must be removed on main thread");
    [self.overlayWindow resignKeyWindow];
    self.overlayWindow.hidden = YES;
    self.overlayWindow = nil;
    self.floatButton = nil;
    self.panelView = nil;
    self.statusLabel = nil;
    self.panelVisible = NO;
    self.status = @"removed";
}

@end
