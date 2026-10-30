#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

@interface HCSafeOverlay : NSObject

- (instancetype)initWithExpectedBundleID:(NSString *)bundleID
                                version:(NSString *)version
                         mappingPassed:(BOOL)mappingPassed;
- (void)installOnMainWindow:(UIWindow *)mainWindow;
- (void)remove;

@property(nonatomic, readonly) BOOL panelVisible;
@property(nonatomic, readonly) NSString *status;

@end

NS_ASSUME_NONNULL_END
