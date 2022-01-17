import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SessionCreatedComponent } from './session-created.component';

describe('SessionCreatedComponent', () => {
  let component: SessionCreatedComponent;
  let fixture: ComponentFixture<SessionCreatedComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ SessionCreatedComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SessionCreatedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
